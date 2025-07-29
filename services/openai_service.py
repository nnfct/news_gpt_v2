import logging
import re
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from core.config import openai_client, openai_keyword_explainer_client, ncs_search_client, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_DEPLOYMENT_NCS, AZURE_OPENAI_KEYWORD_EXPLAINER_DEPLOYMENT

logger = logging.getLogger(__name__)

async def search_ncs_documents(query, top_k=3):
    """Azure AI Search에서 NCS 직무 데이터를 검색하고 관련 문서 반환"""
    if not ncs_search_client:
        logger.warning("NCS Search Client가 초기화되지 않았습니다. 샘플 NCS 데이터를 반환합니다.")
        return [
            {"title": "샘플 NCS 직무: 인공지능 개발자", "content": "인공지능 개발자는 머신러닝 모델 설계, 데이터 분석, AI 시스템 구축 등을 수행합니다. 요구 역량으로는 파이썬, 딥러닝 프레임워크 이해, 데이터 과학 지식 등이 있습니다.", "source": "NCS 샘플"},
            {"title": "샘플 NCS 직무: 빅데이터 분석가", "content": "빅데이터 분석가는 대량의 데이터를 수집, 저장, 처리, 분석하여 비즈니스 의사결정에 필요한 인사이트를 도출합니다. 통계학, 프로그래밍, 데이터베이스 지식이 중요합니다.", "source": "NCS 샘플"}
        ]

    try:
        logger.info(f"🔍 Azure AI Search에서 NCS 데이터 검색 중: '{query}'")
        search_results = await asyncio.to_thread(
            ncs_search_client.search,
            search_text=query,
            query_type="semantic",
            semantic_configuration_name="default",
            search_fields=["content"],
            top=top_k
        )

        docs = []
        for result in search_results:
            docs.append(result.get("content", result.get("text", result.get("description", "내용 없음"))))

        return "\n\n---\n\n".join(docs)
    except Exception as e:
        logger.error(f"❌ Azure AI Search NCS 검색 오류: {e}", exc_info=True)
        return ""

async def get_job_industry_summary(query: str) -> str:
    """사용자 질문에 기반하여 NCS 직무/산업 정보 요약 (AI 활용)"""
    logger.info(f"🧠 get_job_industry_summary 호출 - 쿼리: {query}")
    context_text = await search_ncs_documents(query)

    if not context_text:
        logger.warning("❗ 관련된 직무/산업 정보를 찾을 수 없어 일반 GPT 답변을 시도합니다.")
        system_msg = "너는 직무/산업 관련 전문가 AI야."
        user_prompt = f"'{query}'에 대해 간략하게 요약해줘."
        try:
            response = openai_client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NCS,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=1500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"❌ 샘플 답변 생성 오류: {e}")
            return "관련된 직무/산업 정보를 찾을 수 없고, 요약 생성 중 오류가 발생했습니다."

    system_msg = "너는 직무/산업 관련 문서를 요약하는 AI 직무 분석가야. NCS 문서 기반으로 답변해."
    user_prompt = f"""
    너는 사용자가 입력한 직무/산업 키워드를 기반으로,
    Azure Search에 저장된 NCS 문서에서 관련 정보를 검색하여 요약하는 역할을 수행한다.

    - 아래 결과는 Azure Search를 통해 검색된 문서이다. 반드시 이 내용을 기반으로 정리할 것.
    - 결과가 없으면 “없다”고 하지 말고, 가능한 유사 문서를 참조하여 유추하라.

    [사용자 입력]
    {query}

    [Azure Search 검색 결과]
    {context_text}

    [요약 형식]
    ---
    🔧 직무 개요  
    📚 요구 지식  
    🛠 요구 기술  
    🤝 요구 태도
    """

    try:
        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NCS,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=1500
        )
        summary = response.choices[0].message.content.strip()
        logger.info(f"✅ NCS 요약 성공. 길이: {len(summary)}")
        return summary
    except Exception as e:
        logger.error(f"❌ NCS 직무 요약 오류: {e}", exc_info=True)
        return "NCS 직무 요약 생성 중 오류가 발생했습니다. API 연결 또는 모델 응답을 확인하세요."

async def extract_keywords_with_gpt(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """GPT를 사용해 기사들에서 키워드를 추출하고, 각 키워드 선정 이유를 함께 반환합니다."""
    if not articles:
        logger.warning("❌ 분석할 기사가 없습니다")
        return []

    try:
        top_articles = articles[:10]
        titles_text = "\n".join([f"- {article['title']}" for article in top_articles])

        prompt = f"""다음 IT기술 뉴스 제목에서 핵심 키워드 5개를 추출하고, 각 키워드가 **현재 뉴스에서 주목받는 구체적인 배경이나 동향을 포함하여 선정 이유를 상세히 설명**하세요.

뉴스 제목:
{titles_text}

중요: 마크다운 헤더(#) 사용 금지.
형식:
키워드1: 선정 이유1
키워드2: 선정 이유2
키워드3: 선정 이유3
키워드4: 선정 이유4
키워드5: 선정 이유5
"""
        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "IT기술 키워드 추출 전문가. 각 키워드를 선정한 핵심 이유를 간결하게 설명합니다. 마크다운 헤더 사용 금지."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.2
        )

        keywords_with_reasons_text = response.choices[0].message.content or ""
        logger.info(f"🚀 GPT 키워드 및 이유 추출 완료: \n{keywords_with_reasons_text}")

        keywords = []
        
        processed_text = re.sub(
            r'(키워드(\d+):\s*(.+?))\n\s*(선정 이유\2:\s*(.+?))',
            r'\1 \4',
            keywords_with_reasons_text,
            flags=re.IGNORECASE | re.DOTALL
        )

        lines = processed_text.strip().split('\n')
        filtered_lines = [line.strip() for line in lines if line.strip()]

        for i, line in enumerate(filtered_lines):
            keyword_raw = ""
            reason = "이유 없음"

            if ':' in line:
                first_colon_idx = line.find(':')
                keyword_part = line[:first_colon_idx].strip()
                rest_of_line = line[first_colon_idx+1:].strip()

                reason_match = re.search(r'선정 이유\d+:\s*(.+)', rest_of_line, re.IGNORECASE)
                if reason_match:
                    reason = reason_match.group(1).strip()
                    keyword_raw = re.sub(r'선정 이유\d+:\s*.+', '', rest_of_line, re.IGNORECASE).strip()
                else:
                    reason = rest_of_line
                    keyword_raw = keyword_part
            else:
                keyword_raw = line.strip()
                reason = "GPT가 선정 이유를 제공하지 않았습니다."

            keyword_final = re.sub(r'^(키워드\d+|Keyword\d+|\d+\.)\s*', '', keyword_raw, flags=re.IGNORECASE).strip()
            keyword_final = re.sub(r'^[^\w\s]*', '', keyword_final).strip()
            keyword_final = re.sub(r'[^\w\s\-/가-힣]', '', keyword_final).strip()
            keyword_final = re.sub(r'[:.]$', '', keyword_final).strip()

            if keyword_final and 2 <= len(keyword_final) <= 30:
                keywords.append({
                    "keyword": keyword_final,
                    "reason": reason,
                    "count": 30 - (len(keywords) * 5),
                    "rank": len(keywords) + 1
                })
                if len(keywords) >= 5:
                    break
            else:
                logger.warning(f"⚠️ 유효하지 않은 키워드 파싱됨: 원본:'{line}', 후보:'{keyword_raw}', 최종:'{keyword_final}' (길이/조건 불충족)")

        if len(keywords) < 3:
            logger.warning("⚠️ 키워드 추출 실패 또는 부족, 기본 키워드 사용")
            keywords = [
                {"keyword": "인공지능", "reason": "GPT 응답 파싱 오류 또는 부족으로 인한 기본 키워드", "count": 25, "rank": 1},
                {"keyword": "반도체", "reason": "GPT 응답 파싱 오류 또는 부족으로 인한 기본 키워드", "count": 20, "rank": 2},
                {"keyword": "클라우드", "reason": "GPT 응답 파싱 오류 또는 부족으로 인한 기본 키워드", "count": 15, "rank": 3},
                {"keyword": "빅데이터", "reason": "GPT 응답 파싱 오류 또는 부족으로 인한 기본 키워드", "count": 10, "rank": 4},
                {"keyword": "로봇", "reason": "GPT 응답 파싱 오류 또는 부족으로 인한 기본 키워드", "count": 5, "rank": 5}
            ]
        
        return keywords

    except Exception as e:
        logger.error(f"❌ 키워드 추출 오류: {e}", exc_info=True)
        return [
            {"keyword": "인공지능", "reason": "시스템 오류로 인한 샘플 데이터", "count": 25, "rank": 1},
            {"keyword": "반도체", "reason": "시스템 오류로 인한 샘플 데이터", "count": 20, "rank": 2},
            {"keyword": "클라우드", "reason": "시스템 오류로 인한 샘플 데이터", "count": 15, "rank": 3}
        ]

async def extract_global_keywords_with_gpt(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """GPT를 사용해 해외 기사들에서 영어 키워드를 추출하고, 각 키워드 선정 이유를 함께 반환합니다."""
    if not articles:
        logger.warning("❌ 분석할 해외 기사가 없습니다")
        return []
    
    try:
        top_articles = articles[:10]
        titles_text = "\n".join([f"- {article['title']}" for article in top_articles])

        prompt = f"""Extract 5 key English tech keywords from these global news titles:
For each keyword, provide a **detailed reason explaining its current prominence or relevant trend in the news.**

News Titles:
{titles_text}

Requirements:
- Only English words
- Tech/Technology focused
- No Korean words
- No markdown headers (#)
- Plain text only
Format:
Keyword1: Reason1
Keyword2: Reason2
Keyword3: Reason3
Keyword4: Reason4
Keyword5: Reason5
"""
        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an expert at extracting English tech keywords from global news. Provide concise reasons for each keyword. Use plain text only, no markdown headers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.2
        )
        
        keywords_with_reasons_text = response.choices[0].message.content or ""
        logger.info(f"🌍 해외 GPT 키워드 및 이유 추출 완료: \n{keywords_with_reasons_text}")
        
        keywords = []
        lines = keywords_with_reasons_text.strip().split('\n')
        
        filtered_lines = [line.strip() for line in lines if line.strip()]

        for i, line in enumerate(filtered_lines):
            keyword_raw = ""
            reason = "Reason not provided by AI."
            
            if ':' in line:
                parts = line.split(':', 1)
                keyword_raw = parts[0].strip()
                reason = parts[1].strip()
            else:
                keyword_raw = line.strip()
                reason = "Reason not provided by AI."

            keyword_final = re.sub(r'^(Keyword\d+|\d+\.)\s*:\s*', '', keyword_raw, flags=re.IGNORECASE).strip()
            keyword_final = re.sub(r'^[^\w\s]*', '', keyword_final).strip()
            keyword_final = re.sub(r'[^a-zA-Z0-9\s\-/]', '', keyword_final).strip()
            keyword_final = re.sub(r'[:.]$', '', keyword_final).strip()

            if not keyword_final:
                logger.warning(f"⚠️ Global keyword parsing resulted in empty string: Original:'{line}', Candidate:'{keyword_raw}', Final:'{keyword_final}'")
                continue 

            if keyword_final and 2 <= len(keyword_final) <= 30:
                keywords.append({
                    "keyword": keyword_final,
                    "reason": reason,
                    "count": 30 - (len(keywords) * 5),
                    "rank": len(keywords) + 1
                })
                if len(keywords) >= 5:
                    break
            else:
                logger.warning(f"⚠️ Invalid global keyword parsed: Original:'{line}', Candidate:'{keyword_raw}', Final:'{keyword_final}' (Length/Condition failed)")
        
        if len(keywords) < 3:
            logger.warning("⚠️ Global keyword extraction failed or insufficient, using default keywords.")
            keywords = [
                {"keyword": "AI Technology", "reason": "GPT 응답 파싱 오류 또는 부족으로 인한 기본 키워드", "count": 25, "rank": 1},
                {"keyword": "Innovation", "reason": "GPT 응답 파싱 오류 또는 부족으로 인한 기본 키워드", "count": 20, "rank": 2},
                {"keyword": "Digital Transformation", "reason": "GPT 응답 파싱 오류 또는 부족으로 인한 기본 키워드", "count": 15, "rank": 3},
                {"keyword": "Machine Learning", "reason": "GPT 응답 파싱 오류 또는 부족으로 인한 기본 키워드", "count": 10, "rank": 4},
                {"keyword": "Cloud Computing", "reason": "GPT 응답 파싱 오류 또는 부족으로 인한 기본 키워드", "count": 5, "rank": 5}
            ]

        return keywords

    except Exception as e:
        logger.error(f"❌ 해외 키워드 추출 오류: {e}", exc_info=True)
        return [
            {"keyword": "AI Tech", "reason": "시스템 오류로 인한 샘플 데이터", "count": 25, "rank": 1},
            {"keyword": "Global Innovation", "reason": "시스템 오류로 인한 샘플 데이터", "count": 20, "rank": 2},
            {"keyword": "Digital Future", "reason": "시스템 오류로 인한 샘플 데이터", "count": 15, "rank": 3}
        ]

async def extract_keywords_with_gpt4o(articles):
    """Azure OpenAI GPT-4o로 키워드 추출"""
    
    try:
        articles_text = "\n".join([
            f"제목: {article['title']}\n내용: {article['content'][:200]}..."
            for article in articles[:50]
        ])
        
        prompt = f"""
다음 뉴스 기사들을 분석하고 중요한 키워드를 추출하세요.

기사 내용:
{articles_text}

요구사항:
1. 기업명은 제외하고 기술/산업 관련 키워드 우선 추출
2. 기사에서 자주 언급되는 주요 키워드 추출
3. 응답 형식: 키워드1:빈도1, 키워드2:빈도2 (콤마 구분)
4. 빈도는 5-25 범위
5. 최소 5개 키워드 추출

주요 키워드:
"""
        
        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "뉴스 키워드 분석 전문가입니다. 기사에서 중요한 키워드를 추출합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.2
        )
        
        keywords_text = response.choices[0].message.content or ""
        logger.info(f"GPT-4o 응답: {keywords_text}")
        
        keywords = []
        for item in keywords_text.split(','):
            if ':' in item:
                parts = item.strip().split(':', 1)
                keyword = parts[0].strip()
                try:
                    count = int(parts[1].strip())
                    keywords.append({"keyword": keyword, "count": count})
                except:
                    keywords.append({"keyword": keyword, "count": 10})
        
        if not keywords:
            logger.warning("⚠️ GPT-4o에서 키워드 추출 실패, 기본 키워드 사용")
            keywords = [
                {"keyword": "IT", "count": 20},
                {"keyword": "기술", "count": 18},
                {"keyword": "디지털", "count": 15},
                {"keyword": "정보", "count": 12},
                {"keyword": "시스템", "count": 10}
            ]
        
        keywords.sort(key=lambda x: x['count'], reverse=True)
        
        logger.info(f"✅ {len(keywords)}개 키워드 추출 완료")
        return keywords
        
    except Exception as e:
        logger.error(f"❌ GPT-4o 오류: {e}")
        return []

def extract_keyword_and_industry(question: str) -> Dict[str, Any]:
    """질문에서 키워드와 산업 분류, 그리고 간단한 키워드 선정 이유를 추출"""
    
    industry_keywords = {
        "사회": ["사회", "교육", "일자리", "복지", "정책", "제도", "시민", "공공"],
        "경제": ["경제", "시장", "투자", "금융", "주가", "비용", "수익", "매출", "기업"],
        "IT/과학": ["기술", "개발", "혁신", "연구", "과학", "IT", "소프트웨어", "하드웨어", "플랫폼", "인공지능", "반도체", "클라우드", "메타버스", "블록체인", "AI", "ChatGPT", "머신러닝", "딥러닝", "로봇", "데이터 과학"],
        "생활/문화": ["생활", "문화", "라이프스타일", "소비", "트렌드", "일상", "여가", "엔터테인먼트", "영화", "음악", "게임"],
        "세계": ["글로벌", "국제", "세계", "해외", "수출", "협력", "경쟁", "표준"]
    }
    
    question_lower = question.lower()
    
    detected_industry = None
    for industry, keywords in industry_keywords.items():
        if any(keyword in question_lower for keyword in keywords):
            detected_industry = industry
            break
    
    current_keywords = get_current_weekly_keywords()
    detected_keyword = None
    
    detected_keyword_reason = None

    for keyword in current_keywords:
        if keyword in question:
            detected_keyword = keyword
            match_reason = re.search(f"(최근|새로운|발전|증가|하락|인해|따라|관련하여|대해)\s*(?:{re.escape(keyword)})\s*(.*)", question)
            if match_reason:
                context_word = match_reason.group(1).strip()
                trailing_text = match_reason.group(2).strip()
                if trailing_text:
                    detected_keyword_reason = f"{context_word} {trailing_text}"[:50].strip()
                else:
                    detected_keyword_reason = f"{context_word} 언급"
            else:
                detected_keyword_reason = "질문 내 명시된 이유 없음"
            break
        elif keyword.lower() in question_lower:
            detected_keyword = keyword
            detected_keyword_reason = "질문 내 간접적으로 언급됨"
            break

    question_type = "general"

    comparison_keywords = []
    if "vs" in question_lower or "비교" in question_lower or "차이" in question_lower:
        question_type = "comparison"
        comparison_keywords = [kw for kw in current_keywords if kw.lower() in question_lower]
        if not comparison_keywords and detected_keyword:
            comparison_keywords = [detected_keyword]
        
        if not comparison_keywords:
            match = re.search(r'(.+?)\s*(?:와|와도)\s*(.+?)\s*비교', question_lower)
            if match:
                comparison_keywords = [match.group(1).strip(), match.group(2).strip()]
            else:
                comparison_keywords = current_keywords[:2]

    elif detected_industry and detected_keyword:
        question_type = "industry_analysis"
    elif detected_keyword:
        question_type = "keyword_trend"

    return {
        "type": question_type,
        "keyword": detected_keyword,
        "keywords": comparison_keywords,
        "industry": detected_industry or "사회",
        "reason": detected_keyword_reason
    }

def get_current_weekly_keywords():
    """현재 주간 키워드 가져오기"""
    try:
        return ["인공지능", "반도체", "기술혁신"]
    except Exception as e:
        logger.error(f"키워드 추출 오류: {e}")
        return ["인공지능", "반도체", "기업"]

async def generate_industry_based_answer(question, keyword, industry, current_keywords, reason: Optional[str] = None, ncs_summary_text: Optional[str] = None):
    """
    산업별/직무별 관점 분석 기반 답변 생성 (긍정적 시각, 카테고리별)
    """
    try:
        # 시스템 메시지: '글로벌 Top 컨설팅 펌의 수석 성장 전략가' 페르소나 설정
        system_message_content = (
            "당신은 글로벌 Top 컨설팅 펌의 수석 성장 전략가(Senior Growth Strategist)입니다. "
            "당신의 분석은 항상 최신 시장 데이터에 기반하며, 최대의 성장 기회를 발굴하고 최적의 시나리오를 제시합니다. "
            "답변은 마크다운 헤더(#)를 사용하지 않고, 중간점(·)과 이모지로 구분된 텍스트 형식으로만 생성해야 하며, 다른 부가적인 설명은 절대 추가하지 마십시오."
        )

        # 사용자 프롬프트: '과업 목표', '분석 프레임워크', '답변 형식'을 포함
        keyword_str = keyword # 단일 키워드

        reason_text = ""
        if reason:
            reason_text = f"이 분석 대상 키워드인 '{keyword_str}'은(는) '{reason}'이라는 구체적인 이유로 현재 가장 주목받고 있습니다. 이 맥락을 긍정적 기회 분석에 깊이 활용해주세요."

        # NCS 요약 텍스트를 과업 목표에 직접 삽입
        ncs_specific_context = ""
        if ncs_summary_text:
            # NCS 요약이 있다면, 이 정보를 클라이언트의 직무/산업 배경으로 제시
            ncs_specific_context = f"""
            **클라이언트의 직무/산업 배경:**
            {ncs_summary_text}
            이러한 배경을 가진 클라이언트에게 '{keyword_str}' 트렌드에 내재된,
            """
        else:
            # NCS 요약이 없다면, 기존 industry 인자를 활용 (없을 경우 '산업 전반'으로 대체)
            ncs_specific_context = f"'{industry if industry else '산업 전반'}' 관점에서 '{keyword_str}' 트렌드에 내재된,"
        
        prompt = f"""
### 과업 목표
{ncs_specific_context} **잠재적이고 간과하기 쉬운 긍정적 기회 요소를 다각적으로 분석**하여 보고해주십시오. 분석은 반드시 **객관적이고 현실적인 최적의 시나리오**를 포함해야 합니다.

{reason_text}

### 분석 프레임워크 및 필수 포함 요소 (Analysis Framework)
아래 제시된 4가지 긍정적 기회 카테고리별로 핵심 내용, 발생 가능한 긍정적 시나리오, 그리고 성과 지표를 포함하여 간결하게 작성해주세요. 각 항목당 2~3문장 이내로 작성하며, 전체 답변은 최대 400자(공백 포함)를 넘지 않도록 해주세요.

1.  **기술적/혁신적 기회 (Technological/Innovation Opportunity):** 새로운 기술 도입, 생산성 향상, 연구 개발 가속화, 혁신적인 솔루션 창출.
2.  **시장/경제적 기회 (Market/Economic Opportunity):** 신규 시장 창출, 수익 증대, 비용 절감, 투자 유치, 경쟁 우위 확보.
3.  **사회적/가치적 기회 (Social/Value Opportunity):** 사회 문제 해결 기여, 삶의 질 향상, 윤리적 가치 증진, 긍정적 브랜드 이미지 구축.
4.  **정책적/규제적 기회 (Policy/Regulatory Opportunity):** 정부 지원 및 정책적 우대, 규제 완화, 산업 표준 선도, 국제 협력 증대.

### 답변 형식
· **기술적/혁신적 기회:** 핵심 기회 요약. 긍정적 시나리오 예시: [예시 내용]. 성과 지표: [지표].
· **시장/경제적 기회:** 핵심 기회 요약. 긍정적 시나리오 예시: [예시 내용]. 성과 지표: [지표].
· **사회적/가치적 기회:** 핵심 기회 요약. 긍정적 시나리오 예시: [예시 내용]. 성과 지표: [지표].
· **정책적/규제적 기회:** 핵심 기회 요약. 긍정적 시나리오 예시: [예시 내용]. 성과 지표: [지표].
· **'직무별 기회 활용 전략:** [2~3문장으로 직무 담당자를 위한 구체적인 실행 방안 제시. 이 전략은 해당 직무의 전문성과 연관성을 명확히 보여야 합니다.]
**최종 분석 요약:** [2~3문장으로 전체 긍정적 분석의 핵심 요약 및 기회 활용 방안 포함].
"""

        completion = await asyncio.to_thread( # await asyncio.to_thread 추가
            openai_client.chat.completions.create,
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_message_content},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600, # 넉넉하게 설정 (한글 1자 = 약 2~3토큰)
            temperature=0.3
        )

        response_content = completion.choices[0].message.content
        logger.info(f"✅ 긍정적 분석 보고서 생성 성공. 길이: {len(response_content)}")
        return response_content

    except Exception as e:
        logger.error(f"❌ 긍정적 분석 생성 중 오류: {e}", exc_info=True)
        return f"죄송합니다. 긍정적 분석 보고서 생성 중 오류가 발생했습니다: {str(e)}"


async def generate_keyword_trend_answer(question, keyword):
    """키워드 트렌드 분석 답변 생성"""
    try:
        prompt = f"""
질문: {question}
키워드: {keyword}

'{keyword}'의 최근 트렌드를 분석해주세요.

분석 내용:
· 최근 '{keyword}' 관련 주요 뉴스 동향
· 시간적 변화와 발전 방향
· 향후 전망과 관심 포인트

마크다운 헤더(#) 사용 금지. 중간점(·)과 이모지로 구분하세요.
시간순으로 정리하여 트렌드를 명확하게 설명해주세요.
"""
        
        completion = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": f"당신은 '{keyword}' 분야의 트렌드 분석 전문가입니다. 최신 동향과 변화를 분석합니다. 마크다운 헤더(#) 사용 금지. 중간점(·)과 이모지만 사용하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=16384
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"죄송합니다. '{keyword}' 트렌드 분석 중 오류가 발생했습니다: {str(e)}"

async def generate_comparison_answer(question, keywords, perspective_role: Optional[str] = None, reason: Optional[str] = None):
    """
    주어진 키워드들을 특정 직무/산업 관점에서 비판적/회의적인 시각으로 분석하여
    텍스트 기반의 리스크 분석 보고서를 생성합니다. (긍정적 분석 결과 활용)
    """
    try:
        # 1. 긍정적 분석 결과 받아오기
        positive_analysis_context = ""
        
        # NCS 직무 요약 결과를 저장할 변수 초기화
        ncs_job_summary_for_positive_analysis = None 

        if keywords: # 키워드가 있을 때만 긍정적 분석 호출
            # 여기에서 get_job_industry_summary를 호출하여 NCS 직무/산업 요약을 가져옵니다.
            # 직무명인 perspective_role을 query로 사용합니다.
            try:
                ncs_job_summary_for_positive_analysis = await get_job_industry_summary(perspective_role)
                logger.info(f"NCS Job Summary fetched for positive analysis: {ncs_job_summary_for_positive_analysis[:100]}...")
            except Exception as e:
                logger.error(f"Error fetching NCS job summary for positive analysis: {e}")
                # 오류 발생 시 빈 문자열 또는 기본 메시지로 처리
                ncs_job_summary_for_positive_analysis = "NCS 직무 정보 요약을 가져오는 데 실패했습니다."

            positive_analysis_context = await generate_industry_based_answer(
                question=question,
                keyword=keywords[0],
                industry=perspective_role, # industry는 기존대로 perspective_role 전달
                current_keywords=[],
                reason=reason,
                ncs_summary_text=ncs_job_summary_for_positive_analysis # 여기에 NCS 요약 결과 전달
            )


        # 시스템 메시지: '글로벌 Top 컨설팅 펌의 수석 리스크 분석가' 페르소나 설정
        system_message_content = (
            "당신은 글로벌 Top 컨설팅 펌의 수석 리스크 분석가(Senior Risk Analyst)입니다. "
            "당신의 분석은 항상 최신 데이터에 기반하며, 일반적으로 간과되거나 낙관적으로만 해석되는 면 이면에 숨겨진 리스크를 발굴하고, "
            "최악의 시나리오까지 냉철하게 고려합니다. "
            "답변은 마크다운 헤더(#)를 사용하지 않고, 중간점(·)과 이모지로 구분된 텍스트 형식으로만 생성해야 하며, 다른 부가적인 설명은 절대 추가하지 마십시오."
        )

        # 사용자 프롬프트: '과업 목표', '분석 프레임워크', '답변 형식'을 포함
        keyword_str = ", ".join(keywords)

        reason_text = ""
        if reason and keywords:
            reason_text = f"이 분석 대상 키워드 중 '{keywords[0]}'은(는) '{reason}'이라는 구체적인 이유로 현재 가장 주목받고 있습니다. 이 맥락을 비판적 리스크 분석에 깊이 활용해주세요."

        # NCS 요약 정보를 과업 목표에 직접 삽입
        ncs_specific_client_context = ""
        if ncs_job_summary_for_positive_analysis:
            # NCS 요약이 있다면, 이 정보를 클라이언트의 직무/산업 배경으로 제시
            ncs_specific_client_context = f"""
            **클라이언트의 직무/산업 배경:**
            {ncs_job_summary_for_positive_analysis}
            이러한 배경을 가진 클라이언트가
            """
        else:
            # NCS 요약이 없다면, 기존대로 '산업 전반' 클라이언트로 대체
            ncs_specific_client_context = f"'{perspective_role if perspective_role else '산업 전반'}' 산업의 클라이언트가"


        prompt = f"""
### 과업 목표
{ncs_specific_client_context} '{keyword_str}' 트렌드에 내재된, **간과하기 쉬운 비판적/회의적 관점의 잠재적 리스크**를 다각적으로 분석하여 보고해주십시오. 분석은 반드시 **객관적이고 현실적인 최악의 시나리오**를 포함해야 합니다.

{reason_text}

--- 참고용 긍정적 분석 보고서 (이 내용에 대한 비판적 관점을 제시해주세요) ---
{positive_analysis_context}
---

### 분석 지침 (필수 포함 요소)
위에서 제공된 긍정적 분석 내용을 충분히 참고하여, 그 내용에 대한 반대 의견, 잠재적 문제점, 한계점, 또는 부정적인 영향을 중심으로 핵심 내용을 요약해주세요.
아래 제시된 4가지 리스크 카테고리별로 핵심 내용, 발생 가능한 최악의 시나리오, 그리고 모니터링 지표를 포함하여 간결하게 작성해주세요. 각 항목당 2~3문장 이내로 작성하며, 전체 답변은 최대 400자(공백 포함)를 넘지 않도록 해주세요.

1.  **기술적/운영적 리스크 (Technological/Operational Risk):** 기술 한계, 확장성 문제, 구현의 복잡성, 시스템 오류 가능성, 예상치 못한 운영 문제.
2.  **시장/경제적 리스크 (Market/Economic Risk):** 시장 과열로 인한 버블, 수익 모델의 취약성 및 지속 불가능성, 예상 밖의 높은 비용 또는 투자 회수 지연, 경쟁 심화.
3.  **사회적/윤리적 리스크 (Social/Ethical Risk):** 사회적 불평등 심화, 일자리 감소 및 사회적 혼란, 개인정보 침해 및 데이터 오용, 윤리적 딜레마 (예: 책임 소재), 부정적인 브랜드 이미지 형성.
4.  **규제/법률적 리스크 (Regulatory/Legal Risk):** 예상치 못한 정부 규제 도입 또는 강화, 기존 법규와의 충돌, 지적 재산권 분쟁 가능성, 국제적 규제 장벽.

### 답변 형식
· **기술적/운영적 리스크:** 핵심 리스크 요약. 최악의 시나리오 예시: [예시 내용]. 모니터링 지표: [지표].
· **시장/경제적 리스크:** 핵심 리스크 요약. 최악의 시나리오 예시: [예시 내용]. 모니터링 지표: [지표].
· **사회적/윤리적 리스크:** 핵심 리스크 요약. 최악의 시나리오 예시: [예시 내용]. 모니터링 지표: [지표].
· **규제/법률적 리스크:** 핵심 리스크 요약. 최악의 시나리오 예시: [예시 내용]. 모니터링 지표: [지표].
· **'직무별 기회 활용 전략:** [2~3문장으로 직무 담당자를 위한 구체적인 실행 방안 제시. 이 전략은 해당 직무의 전문성과 연관성을 명확히 보여야 합니다.]

**최종 분석 요약:** [2~3문장으로 전체 리스크 분석의 핵심 요약 및 권고 사항 포함].
"""

        completion = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_message_content},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.3
        )

        response_content = completion.choices[0].message.content
        logger.info(f"✅ 비판적 분석 보고서 생성 성공. 길이: {len(response_content)}")
        return response_content

    except Exception as e:
        logger.error(f"❌ 비판적 분석 생성 중 오류: {e}", exc_info=True)
        return f"죄송합니다. 비판적 분석 보고서 생성 중 오류가 발생했습니다: {str(e)}"


async def generate_contextual_answer(question, current_keywords):
    """현재 키워드 컨텍스트 기반 일반 답변 생성"""
    try:
        keywords_context = f"현재 주간 핵심 키워드: {', '.join(current_keywords)}"
        
        prompt = f"""
질문: {question}
{keywords_context}

현재 주간 핵심 키워드들과 연관지어 답변하되, 질문의 맥락을 정확히 파악하여 답변해주세요.

답변 시 고려사항:
· 현재 주간 핵심 키워드와의 연관성 언급
· 구체적인 사례와 데이터 활용  
· 균형잡힌 시각으로 설명
· 실용적인 정보 제공

마크다운 헤더(#) 사용 금지. 중간점(·)과 이모지로 구분하세요.
명확하고 도움이 되는 답변을 제공해주세요.
"""
        
        completion = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": f"당신은 뉴스 분석 전문가입니다. 현재 주간 핵심 키워드({', '.join(current_keywords)})를 고려하여 질문에 답변합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=16384
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"

def analyze_keyword_dynamically(request: dict):
    """동적 키워드 분석 - 클릭된 키워드에 대한 다각도 분석"""
    keyword = request.get("keyword", "")
    
    if not keyword:
        raise HTTPException(status_code=400, detail="키워드를 제공해야 합니다.")
    
    try:
        prompt = f"""
키워드: '{keyword}'

다음 5가지 관점에서 이 키워드를 분석해주세요:
· 사회적 영향
· 경제적 측면  
· 기술적 관점
· 문화적 의미
· 미래 전망

각 관점별로 2-3문장씩 간결하게 설명해주세요.
마크다운 헤더(#) 사용 금지. 중간점(·)과 이모지만 사용하세요.
"""
        
        completion = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "당신은 다양한 관점에서 키워드를 분석하는 전문가입니다. 마크다운 헤더(#) 사용 금지. 중간점(·)과 이모지로 구분하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )
        
        return {
            "keyword": keyword,
            "analysis": completion.choices[0].message.content
        }
        
    except Exception as e:
        return {
            "keyword": keyword,
            "analysis": f"키워드 분석 중 오류가 발생했습니다: {str(e)}"
        }

async def generate_weekly_insight(keywords_data):
    """주간 인사이트 생성 (개선된 구조)"""
    try:
        domestic_details = [f"{k['keyword']} ({k['count']}건)" for k in keywords_data["domestic_keywords"]]
        global_details = [f"{k['keyword']} ({k['count']}건)" for k in keywords_data["global_keywords"]]

        prompt = f"""
        AI 뉴스 구독자들을 위한 주간 인사이트를 작성해주세요. 전문적이면서도 읽기 쉽게 작성해주세요.

        📊 이번 주 분석 데이터:
        · 분석 기간: {keywords_data["period"]}
        · 국내 TOP 키워드: {", ".join(domestic_details)}
        · 해외 TOP 키워드: {", ".join(global_details)}

        다음 구조로 작성해주세요:

        � 이번 주 핫 키워드

        📈 국내 기술 동향
        · 가장 주목받은 키워드와 그 배경
        · 관련 산업/기업에 미치는 영향
        · 실무진이 알아야 할 포인트

        🌍 글로벌 기술 트렌드
        · 해외에서 화제가 된 기술 이슈
        · 국내 시장에 미칠 영향 예측
        · 글로벌 vs 국내 트렌드 비교

        💡 다음 주 전망 및 실행 포인트
        · 주목해야 할 기술/키워드
        · 비즈니스 기회나 위험 요소
        · 실무진을 위한 액션 아이템

        🎯 한 줄 요약
        · 이번 주 가장 중요한 인사이트를 한 문장으로

        ⚠️ 중요: 마크다운 헤더 기호 절대 사용하지 말고, 이모지와 중간점만 사용해서 구분해주세요.
        전체 분량: 1000자 내외로 작성해주세요.
        """

        completion = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "당신은 AI 뉴스 분석 전문가입니다. 주간 인사이트를 구독자들에게 제공합니다. 마크다운 헤더(#) 절대 사용 금지. 대신 이모지와 중간점(·)만 사용하여 구분하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )

        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ 주간 인사이트 생성 오류: {e}")
        return """
🔍 이번 주 AI 뉴스 하이라이트

� 국내 기술 트렌드
• 인공지능과 반도체 분야의 지속적인 성장
• 기술 혁신과 산업 변화 가속화
• 정부 정책과 기업 투자 확대

� 글로벌 기술 동향
• AI 기술의 전 산업 확산
• 글로벌 기술 경쟁 심화
• 신기술 도입과 활용 사례 증가

💡 주간 인사이트
이번 주는 AI와 반도체 기술이 주요 화두였습니다. 국내외 모두 기술 혁신에 대한 관심이 높아지고 있어 관련 산업의 성장이 기대됩니다.

🎯 다음 주 전망
• AI 기술 발전 지속 관찰 필요
• 관련 투자 기회 모니터링 권장

📧 News GPT v2 팀 드림
        """


async def get_gpt_commentary(trend_request):
    """GPT를 사용하여 트렌드에 대한 해설 생성"""
    try:
        if not trend_request.headlines:
            return {"comment": "관련 뉴스가 없어 트렌드 해설을 제공할 수 없습니다.", "status": "no_news"}

        prompt = (
            f"The following are recent news headlines related to the keyword '{trend_request.keyword}':\n"
            + "\n".join(f"- {title}" for title in trend_request.headlines)
            + "\n\nBased on these headlines, explain why people are likely searching for this keyword.\n\n"
            "🧠 Output format:\n"
            "1. A one-sentence summary of the main reason for the keyword being searched.\n"
            "2. A short paragraph elaborating on the reason, based on the headlines.\n\n"
            "📌 Rules:\n"
            "- All output must be in Korean.\n"
            "- Do NOT mention 'Google Trends' anywhere in the answer.\n"
            "- If the headlines are insufficient to determine a clear reason, you may use general web knowledge to supplement your explanation.\n"
            "- In that case, please add the following sentence at the end of the paragraph:\n"
            "  ※ 기사 제목만으로는 유의미한 검색 원인을 찾기 어려워, 추가 정보를 참고했습니다."
        )
        response = openai_keyword_explainer_client.chat.completions.create(
            model=AZURE_OPENAI_KEYWORD_EXPLAINER_DEPLOYMENT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=16384
        )

        logger.info(f"GPT Commentary Response: {response.choices[0].message.content}")
        
        return response.choices[0].message.content or "No commentary generated."
    except Exception as e:
        logger.error(f"Error generating GPT commentary: {e}", exc_info=True)
        return "Failed to generate commentary due to a server error." 
    


