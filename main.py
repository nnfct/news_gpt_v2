import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import openai
from collections import Counter

app = FastAPI()

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

load_dotenv()


AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

if not all([AZURE_SEARCH_API_KEY, AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT]):
    raise RuntimeError("환경변수(.env) 값이 모두 설정되어야 합니다.")

search_client = SearchClient(
    endpoint=str(AZURE_SEARCH_ENDPOINT),
    index_name=str(AZURE_SEARCH_INDEX),
    credential=AzureKeyCredential(str(AZURE_SEARCH_API_KEY))
)

@app.get("/weekly-summary")
def get_weekly_summary():
    """주간 키워드 요약 조회"""
    try:
        # 주간 요약 데이터 검색 (더 구체적으로)
        results = search_client.search(
            search_text="",  # 빈 검색으로 모든 문서 대상
            filter="id eq 'weekly_summary_2025_week3'",  # 정확한 ID로 필터링
            top=1
        )
        
        for doc in results:
            return {
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "date": doc.get("date", "")
            }
                
        return {"title": "주간 요약 없음", "content": "아직 분석된 주간 데이터가 없습니다.", "date": ""}
    except Exception as e:
        return {"title": "오류", "content": f"주간 요약 조회 중 오류 발생: {str(e)}", "date": ""}

@app.get("/section-analysis/{section}")
def get_section_analysis(section: str):
    """키워드에 대한 산업별 시각 분석"""
    
    try:
        # 현재 주간 키워드 가져오기
        weekly_results = search_client.search(search_text="weekly_summary", top=1)
        current_keywords = ["AI", "인공지능", "반도체"]  # 기본값
        
        for doc in weekly_results:
            content = doc.get("content", "")
            # content에서 키워드 추출
            import re
            keyword_match = re.findall(r'\[(.*?)\]', content)
            if keyword_match and len(keyword_match) >= 3:
                current_keywords = keyword_match[:3]
            break
        
        # 키워드들을 조합한 컨텍스트
        keywords_text = ", ".join(current_keywords)
        
        # 해당 키워드 관련 기사들 수집
        results = search_client.search(
            search_text=keywords_text,
            top=10
        )
        
        # 기사들의 내용을 컨텍스트로 수집
        articles_content = []
        for doc in results:
            content = doc.get("content", "")
            if content:
                articles_content.append(content)
        
        context = "\n".join(articles_content[:5])  # 상위 5개 기사만 사용
        
        if not context.strip():
            return {
                "section": section,
                "keywords": current_keywords,
                "analysis": f"현재 주요 키워드({keywords_text})에 대한 {section} 시각의 분석 데이터가 부족합니다.",
                "summary": "더 많은 데이터가 필요합니다."
            }
        
        # LLM을 통한 키워드별 산업 시각 분석
        analysis = generate_keyword_section_analysis(section, current_keywords, context)
        
        return {
            "section": section,
            "keywords": current_keywords,
            "analysis": analysis,
            "summary": f"{section} 시각에서 본 주요 키워드 분석 완료"
        }
        
    except Exception as e:
        return {
            "section": section, 
            "keywords": [],
            "analysis": f"분석 중 오류가 발생했습니다: {str(e)}",
            "summary": "오류 발생"
        }

def generate_keyword_section_analysis(section: str, keywords: list, context: str):
    """키워드에 대한 산업별 시각 분석 생성"""
    import openai
    openai.api_type = "azure"
    openai.api_key = AZURE_OPENAI_API_KEY
    openai.azure_endpoint = AZURE_OPENAI_ENDPOINT
    openai.api_version = "2024-02-15-preview"
    
    keywords_text = ", ".join(keywords)
    
    # 섹션별 관점 정의
    section_perspectives = {
        "사회": "사회적 영향, 일자리 변화, 교육, 디지털 격차, 윤리적 측면",
        "경제": "경제적 파급효과, 시장 규모, 투자 동향, 산업 성장, 비용 효율성",
        "IT과학": "기술적 혁신, 연구개발 동향, 기술 표준, 특허, 기술적 한계와 발전방향",
        "세계": "글로벌 경쟁력, 국가간 기술 격차, 국제 협력, 표준화, 지정학적 영향",
        "생활문화": "일상생활 변화, 소비자 행동, 문화적 수용성, 라이프스타일 개선"
    }
    
    perspective = section_perspectives.get(section, f"{section} 분야의 전문적 관점")
    
    prompt = f"""
주요 키워드: {keywords_text}

위 키워드들에 대해 {section} 분야의 관점에서 분석해주세요.
분석 관점: {perspective}

다음 뉴스 데이터를 참고하여 분석하세요:
{context}

분석 형식:
1. {section} 관점에서 본 주요 키워드의 의미 (2-3줄)
2. {section} 분야에 미치는 영향 (2-3줄)
3. {section} 측면에서의 전망과 과제 (2-3줄)

전문적이고 구체적으로 분석해주세요.
"""
    
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"당신은 {section} 분야의 전문 분석가입니다. 주어진 키워드들을 {section} 관점에서 심층 분석하는 역할을 합니다."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"분석 생성 중 오류가 발생했습니다: {str(e)}"

@app.post("/chat")
def chat(query: dict):
    # 벡터 검색 대신 텍스트 검색 사용 (임시)
    question = query.get("question", "")
    
    # 텍스트 기반 검색
    results = search_client.search(
        search_text=question,
        top=3
    )
    context = "\n".join([doc.get("content", "") for doc in results])
    
    # 답변 생성
    answer = generate_answer(question, context)
    return {"answer": answer}

def get_embedding(text):
    # Azure OpenAI text-embedding-ada-002로 임베딩 생성
    import openai
    openai.api_type = "azure"
    openai.api_key = AZURE_OPENAI_API_KEY
    openai.azure_endpoint = AZURE_OPENAI_ENDPOINT
    openai.api_version = "2024-02-15-preview"
    try:
        response = openai.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임베딩 생성 오류: {e}")

def generate_answer(question, context):
    # Azure OpenAI GPT-4o로 답변 생성
    import openai
    openai.api_type = "azure"
    openai.api_key = AZURE_OPENAI_API_KEY
    openai.azure_endpoint = AZURE_OPENAI_ENDPOINT
    openai.api_version = "2024-02-15-preview"
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "아래 컨텍스트를 참고해 질문에 답하세요."},
                {"role": "user", "content": f"컨텍스트: {context}\n\n질문: {question}"}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"답변 생성 오류: {e}")

# 새로운 엔드포인트들 추가

@app.get("/weekly-keywords")
def get_weekly_keywords():
    """주간 Top 3 키워드 반환"""
    try:
        # Azure Search에서 모든 기사 가져오기
        results = search_client.search(search_text="*", top=100)
        
        # 모든 키워드 수집
        all_keywords = []
        for doc in results:
            content = doc.get("content", "")
            # "핵심 키워드: " 부분에서 키워드 추출
            if "핵심 키워드:" in content:
                keywords_text = content.split("핵심 키워드:")[1].strip()
                keywords = [k.strip() for k in keywords_text.split(",")]
                all_keywords.extend(keywords)
        
        # 키워드 빈도 계산 및 Top 3 선택
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        top_keywords = [keyword for keyword, count in keyword_counts.most_common(3)]
        
        return {
            "keywords": top_keywords,
            "week_info": "7월 3주차 (2025.07.11~07.17) - AI 뉴스 분석"
        }
    except Exception as e:
        # 오류 시 샘플 데이터 반환
        return {
            "keywords": ["인공지능", "반도체", "기업"],
            "week_info": "7월 3주차 (2025.07.11~07.17) - AI 뉴스 분석"
        }

@app.post("/industry-analysis")
def get_industry_analysis(request: dict):
    """산업별 키워드 분석 (기존 + 정반대 관점)"""
    industry = request.get("industry", "")
    keyword = request.get("keyword", "")
    
    if not industry or not keyword:
        raise HTTPException(status_code=400, detail="산업과 키워드를 모두 제공해야 합니다.")
    
    # 기존 분석 프롬프트
    industry_prompts = {
        "사회": f"'{keyword}'에 대한 사회적 관점에서의 분석을 제공해주세요. 사회 구조, 시민 생활, 사회 문제 해결 등의 측면에서 3-4문장으로 설명해주세요.",
        "경제": f"'{keyword}'에 대한 경제적 관점에서의 분석을 제공해주세요. 시장 영향, 투자 전망, 산업 파급효과 등의 측면에서 3-4문장으로 설명해주세요.",
        "IT/과학": f"'{keyword}'에 대한 IT/과학 기술적 관점에서의 분석을 제공해주세요. 기술 발전, 혁신 동향, 기술적 과제 등의 측면에서 3-4문장으로 설명해주세요.",
        "생활/문화": f"'{keyword}'에 대한 생활/문화적 관점에서의 분석을 제공해주세요. 일상 생활 변화, 문화적 영향, 라이프스타일 등의 측면에서 3-4문장으로 설명해주세요.",
        "세계": f"'{keyword}'에 대한 글로벌/국제적 관점에서의 분석을 제공해주세요. 국제 동향, 글로벌 경쟁, 외교적 영향 등의 측면에서 3-4문장으로 설명해주세요."
    }
    
    # 정반대 관점 프롬프트
    counter_prompts = {
        "사회": f"'{keyword}'에 대한 비판적/회의적 사회 관점을 제시해주세요. 사회적 우려, 부작용, 격차 심화 등의 측면에서 3-4문장으로 설명해주세요.",
        "경제": f"'{keyword}'에 대한 경제적 리스크와 부정적 영향을 분석해주세요. 시장 불안정성, 투자 위험, 경제적 부작용 등의 측면에서 3-4문장으로 설명해주세요.",
        "IT/과학": f"'{keyword}'에 대한 기술적 한계와 문제점을 분석해주세요. 기술적 위험, 윤리적 문제, 발전 장애물 등의 측면에서 3-4문장으로 설명해주세요.",
        "생활/문화": f"'{keyword}'에 대한 문화적 저항과 생활상의 문제를 분석해주세요. 전통 문화 충돌, 생활 불편, 문화적 부작용 등의 측면에서 3-4문장으로 설명해주세요.",
        "세계": f"'{keyword}'에 대한 국제적 갈등과 부정적 영향을 분석해주세요. 국가간 분쟁, 글로벌 불평등, 국제적 우려 등의 측면에서 3-4문장으로 설명해주세요."
    }
    
    main_prompt = industry_prompts.get(industry, f"'{keyword}'에 대한 {industry} 관점에서의 분석을 제공해주세요.")
    counter_prompt = counter_prompts.get(industry, f"'{keyword}'에 대한 {industry} 관점에서의 반대 의견을 제공해주세요.")
    
    try:
        import openai
        openai.api_type = "azure"
        openai.api_key = AZURE_OPENAI_API_KEY
        openai.azure_endpoint = AZURE_OPENAI_ENDPOINT
        openai.api_version = "2024-02-15-preview"
        
        # 기존 분석
        main_completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"{industry} 분야 전문가로서 키워드에 대한 긍정적 분석을 제공합니다."},
                {"role": "user", "content": main_prompt}
            ]
        )
        
        # 정반대 관점 분석
        counter_completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"{industry} 분야의 비판적 시각을 가진 전문가로서 반대 의견을 제시합니다."},
                {"role": "user", "content": counter_prompt}
            ]
        )
        
        return {
            "analysis": main_completion.choices[0].message.content,
            "counter_analysis": counter_completion.choices[0].message.content
        }
    except Exception as e:
        return {
            "analysis": f"분석을 생성하는 중 오류가 발생했습니다: {str(e)}",
            "counter_analysis": "반대 의견을 생성할 수 없습니다."
        }

@app.get("/keyword-articles")
def get_keyword_articles(keyword: str):
    """키워드 관련 기사 Top 5 조회"""
    try:
        # 키워드로 기사 검색
        results = search_client.search(
            search_text=keyword,
            top=10,
            select=["title", "content", "date"]
        )
        
        articles = []
        for doc in results:
            if len(articles) >= 5:
                break
                
            title = doc.get("title", "")
            content = doc.get("content", "")
            date = doc.get("date", "")
            
            if title and content:
                # 간단한 요약 (처음 200자)
                summary = content[:200] + "..." if len(content) > 200 else content
                
                articles.append({
                    "title": title,
                    "summary": summary,
                    "date": date or "날짜 정보 없음"
                })
        
        if not articles:
            # 샘플 데이터 반환
            articles = [
                {
                    "title": f"'{keyword}' 관련 뉴스 1",
                    "summary": f"{keyword}에 대한 최신 동향과 관련된 주요 내용을 다룬 기사입니다.",
                    "date": "2025-07-17"
                },
                {
                    "title": f"'{keyword}' 관련 뉴스 2", 
                    "summary": f"{keyword} 분야의 새로운 발전과 전망에 대해 분석한 기사입니다.",
                    "date": "2025-07-16"
                }
            ]
        
        return {"articles": articles}
    except Exception as e:
        print(f"키워드 기사 검색 오류: {e}")
        return {
            "articles": [
                {
                    "title": "검색 오류",
                    "summary": f"'{keyword}' 관련 기사를 불러오는 중 오류가 발생했습니다.",
                    "date": "오류"
                }
            ]
        }

def calculate_relevance_score(title, content, keyword):
    """키워드 관련성 점수 계산"""
    score = 0
    keyword_lower = keyword.lower()
    title_lower = title.lower()
    content_lower = content.lower()
    
    # 제목에 키워드가 있으면 높은 점수
    if keyword_lower in title_lower:
        score += 3
    
    # 내용에서 키워드 등장 횟수
    score += content_lower.count(keyword_lower)
    
    return score

def generate_article_summary(title, content, keyword):
    """기사 요약 생성 (키워드 중심)"""
    try:
        import openai
        openai.api_type = "azure"
        openai.api_key = AZURE_OPENAI_API_KEY
        openai.azure_endpoint = AZURE_OPENAI_ENDPOINT
        openai.api_version = "2024-02-15-preview"
        
        prompt = f"""
다음 기사를 '{keyword}' 키워드 중심으로 2-3문장으로 간결하게 요약해주세요.

제목: {title}
내용: {content[:500]}

요약시 다음을 포함해주세요:
1. {keyword}와 관련된 핵심 내용
2. 주요 동향이나 변화
3. 영향이나 전망

간결하고 명확하게 작성해주세요.
"""
        
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "뉴스 기사를 키워드 중심으로 간결하고 정확하게 요약하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        print(f"요약 생성 오류: {e}")
        return content[:100] + "..."
