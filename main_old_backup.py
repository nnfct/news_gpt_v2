import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from collections import Counter
import requests
import json
import time
from datetime import datetime, timedelta
import uvicorn
from error_logger import log_error, auto_log_errors
from typing import Optional

app = FastAPI()

# 글로벌 예외 처리기 추가
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """모든 예외를 자동으로 error_history.md에 기록"""
    
    # 에러 로깅
    log_error(
        error=exc,
        file_name="main.py",
        function_name="global_exception_handler",
        context=f"글로벌 예외 처리 - 요청 URL: {request.url}",
        additional_info={
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else "unknown"
        },
        severity="HIGH"
    )
    
    # 클라이언트에게 에러 응답
    return JSONResponse(
        status_code=500,
        content={
            "error": "내부 서버 오류가 발생했습니다.",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

load_dotenv()

# 환경변수 로드
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

# DeepSearch API 설정
DEEPSEARCH_API_KEY = os.getenv("DEEPSEARCH_API_KEY")

if not all([AZURE_SEARCH_API_KEY, AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT]):
    raise RuntimeError("환경변수(.env) 값이 모두 설정되어야 합니다.")

# Azure OpenAI 클라이언트 초기화
openai_client = AzureOpenAI(
    api_key=str(AZURE_OPENAI_API_KEY),
    api_version="2024-02-15-preview",
    azure_endpoint=str(AZURE_OPENAI_ENDPOINT)
)

search_client = SearchClient(
    endpoint=str(AZURE_SEARCH_ENDPOINT),
    index_name=str(AZURE_SEARCH_INDEX),
    credential=AzureKeyCredential(str(AZURE_SEARCH_API_KEY))
)

def get_current_week_news_from_deepsearch(query, start_date=None, end_date=None):
    """DeepSearch API를 사용하여 현재 주간 뉴스 가져오기"""
    if not DEEPSEARCH_API_KEY:
        print("DeepSearch API 키가 설정되지 않았습니다.")
        return []
    
    # 현재 주간 날짜 설정 (2025년 7월 3주차)
    if not start_date:
        start_date = "2025-07-14"  # 7월 3주차 시작
    if not end_date:
        end_date = "2025-07-20"    # 7월 3주차 종료
    
    try:
        # 먼저 단순 키워드로 검색 시도
        simple_query = query
        print(f"🔍 단순 검색어 시도: {simple_query}")
        
        # DeepSearch API 호출 (한국어 기사 우선 사용)
        url = "https://api-v2.deepsearch.com/v1/articles"
        params = {
            "api_key": DEEPSEARCH_API_KEY,
            "q": simple_query,
            "limit": 20,  # 가져올 뉴스 수
            "start_date": start_date,
            "end_date": end_date,
            "sort": "published_at:desc"  # 최신순 정렬
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        articles = []
        
        # 단순 검색 결과 확인
        simple_articles = []
        for item in data.get("data", []):
            # 날짜 필터링 (API에서 이미 필터링되지만 추가 확인)
            pub_date = item.get("published_at", "") or item.get("date", "")
            
            try:
                # ISO 형식 날짜 파싱
                if "T" in pub_date:
                    article_date = pub_date.split("T")[0]  # YYYY-MM-DD 형식으로 추출
                else:
                    article_date = pub_date
                
                # 지정된 주간 범위 내의 뉴스만 필터링
                if start_date <= article_date <= end_date:
                    # content_url 필드 사용 (실제 기사 URL)
                    article_url = item.get("content_url", "") or item.get("url", "") or item.get("link", "")
                    
                    # 기사 관련성 검사
                    title = item.get("title", "")
                    summary = item.get("summary", "") or (item.get("content", "") or "")[:200] + "..."
                    
                    # 관련성 점수 계산 및 필터링
                    relevance_score = calculate_article_relevance(title, summary, query)
                    
                    # 더 관대한 관련성 필터링 적용
                    if relevance_score >= 0.1:  # 임계값을 0.1로 하향 조정
                        simple_articles.append({
                            "title": title,
                            "description": summary,
                            "link": article_url,
                            "pubDate": article_date,
                            "relevance": relevance_score
                        })
                        print(f"    📰 기사 추가: {title[:30]}... (점수: {relevance_score:.2f})")
                    else:
                        print(f"    ❌ 관련성 낮음: {title[:30]}... (점수: {relevance_score:.2f})")
            except Exception as e:
                print(f"날짜 파싱 오류: {e}")
                continue
        
        # 단순 검색에서 충분한 결과를 얻었다면 사용
        if len(simple_articles) >= 3:
            articles = simple_articles
            print(f"✅ 단순 검색으로 {len(articles)}개 관련 기사 발견")
        else:
            print(f"⚠️ 단순 검색 결과 부족 ({len(simple_articles)}개), Enhanced 검색 시도")
            
            # Enhanced 검색 시도
            enhanced_query = enhance_company_search_query(query)
            print(f"🔍 향상된 검색어: {query} → {enhanced_query}")
            
            params["q"] = enhanced_query
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            enhanced_articles = []
            
            for item in data.get("data", []):
                pub_date = item.get("published_at", "") or item.get("date", "")
                
                try:
                    if "T" in pub_date:
                        article_date = pub_date.split("T")[0]
                    else:
                        article_date = pub_date
                    
                    if start_date <= article_date <= end_date:
                        article_url = item.get("content_url", "") or item.get("url", "") or item.get("link", "")
                        title = item.get("title", "")
                        summary = item.get("summary", "") or (item.get("content", "") or "")[:200] + "..."
                        
                        relevance_score = calculate_article_relevance(title, summary, query)
                        
                        if relevance_score >= 0.1:
                            enhanced_articles.append({
                                "title": title,
                                "description": summary,
                                "link": article_url,
                                "pubDate": article_date,
                                "relevance": relevance_score
                            })
                            print(f"    📰 Enhanced 기사 추가: {title[:30]}... (점수: {relevance_score:.2f})")
                        else:
                            print(f"    ❌ Enhanced 관련성 낮음: {title[:30]}... (점수: {relevance_score:.2f})")
                except Exception as e:
                    print(f"Enhanced 날짜 파싱 오류: {e}")
                    continue
            
            # 단순 검색과 Enhanced 검색 결과 결합
            all_articles = simple_articles + enhanced_articles
            
            # 중복 제거 (제목 기준)
            seen_titles = set()
            articles = []
            for article in all_articles:
                if article["title"] not in seen_titles:
                    seen_titles.add(article["title"])
                    articles.append(article)
        
        # 관련성 점수 순으로 정렬
        articles.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        
        return articles[:10]  # 최대 10개 반환
        
    except Exception as e:
        log_error(
            error=e,
            file_name="main.py",
            function_name="get_current_week_news_from_deepsearch",
            context=f"DeepSearch API 호출 오류 - 쿼리: {query}, 기간: {start_date}~{end_date}",
            additional_info={
                "query": query,
                "start_date": start_date,
                "end_date": end_date,
                "has_api_key": bool(DEEPSEARCH_API_KEY)
            },
            severity="HIGH"
        )
        print(f"DeepSearch API 호출 오류: {e}")
        return []

def enhance_company_search_query(query):
    """기업명 검색을 위한 쿼리 향상"""
    
    # 주요 기업별 검색어 매핑
    company_queries = {
        "DB": '"DB금융투자" OR "DB손해보험" OR "DB그룹" OR "DB금융" OR "DB하이텍"',
        "NAVER": '"네이버" OR "NAVER" OR "네이버웹툰" OR "네이버클라우드"',
        "삼성전자": '"삼성전자" OR "삼성" OR "Samsung Electronics"',
        "한화": '"한화그룹" OR "한화시스템" OR "한화오션" OR "한화생명"',
        "LG": '"LG전자" OR "LG화학" OR "LG에너지솔루션" OR "LG유플러스"',
        "현대차": '"현대자동차" OR "현대차" OR "현대모비스"',
        "SK": '"SK텔레콤" OR "SK하이닉스" OR "SKT" OR "SK이노베이션"',
        "NEW": '"NEW" OR "뉴스" OR "신규"'  # NEW는 너무 일반적이므로 제외
    }
    
    # 매핑된 쿼리가 있으면 사용, 없으면 원본 쿼리 사용
    return company_queries.get(query, f'"{query}"')

def calculate_article_relevance(title, content, keyword):
    """기사와 키워드의 관련성 점수 계산"""
    
    # 기본 점수
    score = 0.0
    
    # 제목과 내용을 소문자로 변환
    title_lower = title.lower()
    content_lower = content.lower()
    keyword_lower = keyword.lower()
    
    print(f"    🔍 관련성 계산: '{keyword}' vs '{title[:50]}...'")
    
    # 정확한 키워드 매칭 (가중치 높임)
    if keyword_lower in title_lower:
        score += 1.0  # 제목에 있으면 높은 점수
        print(f"    ✅ 제목에서 키워드 발견: +1.0")
    
    if keyword_lower in content_lower:
        score += 0.5  # 내용에 있으면 중간 점수
        print(f"    ✅ 내용에서 키워드 발견: +0.5")
    
    # 특정 기업별 관련 키워드 체크 (더 강화)
    related_keywords = {
        "db": ["db금융투자", "db손해보험", "db그룹", "db생명", "db하이텍", "db증권", "디비금융", "디비그룹"],
        "naver": ["네이버", "naver", "네이버웹툰", "네이버클라우드", "네이버페이", "라인"],
        "삼성전자": ["삼성전자", "삼성", "samsung", "갤럭시", "반도체", "메모리", "스마트폰"],
        "한화": ["한화그룹", "한화시스템", "한화오션", "한화생명", "한화화학", "한화솔루션"],
        "lg": ["lg전자", "lg화학", "lg에너지솔루션", "lg유플러스", "엘지"],
        "현대차": ["현대자동차", "현대차", "현대모비스", "제네시스", "아이오닉"],
        "sk": ["sk텔레콤", "sk하이닉스", "skt", "sk이노베이션", "sk바이오팜"]
    }
    
    # 키워드 정규화 (괄호 제거 등)
    clean_keyword = keyword_lower.split('(')[0].strip()
    
    if clean_keyword in related_keywords:
        print(f"    🔍 관련 키워드 목록 확인: {related_keywords[clean_keyword]}")
        for related_word in related_keywords[clean_keyword]:
            if related_word in title_lower or related_word in content_lower:
                score += 0.3  # 관련 키워드 발견 시 점수 추가
                print(f"    💡 관련 키워드 발견: {related_word} (+0.3)")
                break
    
    # 부정적 키워드 (무관한 내용) 체크
    negative_keywords = [
        "콘서트", "k-pop", "아이돌", "드라마", "영화", "연예", "예능", "스포츠",
        "축구", "야구", "올림픽", "게임", "리그오브레전드", "롤", "배틀그라운드",
        "요리", "레시피", "맛집", "여행", "관광", "패션", "뷰티", "코스메틱"
    ]
    
    for neg_word in negative_keywords:
        if neg_word in title_lower or neg_word in content_lower:
            score -= 0.5  # 무관한 키워드 발견 시 점수 감점
            print(f"    ⚠️ 무관한 키워드 발견: {neg_word} (-0.5)")
            break
    
    print(f"    📊 최종 점수: {max(0.0, score):.2f}")
    return max(0.0, score)  # 음수 점수 방지

def get_weekly_hot_keywords_from_aggregation(start_date, end_date):
    """DeepSearch API로 뉴스 수집 → Azure AI Search 업로드 → GPT-4o 키워드 추출 → Top 5 선정"""
    
    try:
        print(f"🔍 올바른 플로우 시작: {start_date} ~ {end_date}")
        
        # 1️⃣ DeepSearch API로 IT/기술 뉴스 수집
        print("\n1️⃣ DeepSearch API 뉴스 수집 중...")
        articles = collect_it_news_from_deepsearch(start_date, end_date)
        
        if not articles:
            print("❌ 뉴스 수집 실패, 기본 키워드 반환")
            return [
                {"keyword": "인공지능", "count": 25, "source": "IT기술"},
                {"keyword": "반도체", "count": 20, "source": "IT기술"},
                {"keyword": "클라우드", "count": 18, "source": "IT기술"},
                {"keyword": "메타버스", "count": 15, "source": "IT기술"},
                {"keyword": "블록체인", "count": 12, "source": "IT기술"}
            ]
        
        # 2️⃣ Azure AI Search에 업로드
        print(f"\n2️⃣ Azure AI Search 업로드 중 ({len(articles)}개 기사)...")
        upload_success = upload_articles_to_azure_search(articles)
        
        # 3️⃣ Azure OpenAI GPT-4o로 키워드 추출
        print(f"\n3️⃣ GPT-4o 키워드 추출 중...")
        keywords = extract_keywords_with_gpt4o(articles)
        
        # 4️⃣ 키워드 빈도 분석 및 Top 5 선정
        print(f"\n4️⃣ 키워드 빈도 분석 중...")
        top_keywords = analyze_keyword_frequency(keywords)
        
        print(f"🎯 최종 Top 5 키워드 (실제 뉴스 기반):")
        for i, kw in enumerate(top_keywords[:5], 1):
            print(f"  {i}. {kw['keyword']} ({kw['count']}회)")
        
        return top_keywords[:5]
        
    except Exception as e:
        print(f"❌ 키워드 추출 오류: {e}")
        return [
            {"keyword": "인공지능", "count": 25, "source": "IT기술"},
            {"keyword": "반도체", "count": 20, "source": "IT기술"},
            {"keyword": "클라우드", "count": 18, "source": "IT기술"},
            {"keyword": "메타버스", "count": 15, "source": "IT기술"},
            {"keyword": "블록체인", "count": 12, "source": "IT기술"}
        ]

def collect_it_news_from_deepsearch(start_date, end_date):
    """DeepSearch API로 IT/기술 뉴스 수집"""
    if not DEEPSEARCH_API_KEY:
        print("❌ DeepSearch API 키 없음")
        return []
    
    try:
        articles = []
        tech_keywords = [
            "인공지능", "AI", "머신러닝", "딥러닝", "반도체", "칩", "프로세서", 
            "클라우드", "데이터센터", "소프트웨어", "5G", "6G", "블록체인", 
            "메타버스", "VR", "AR", "로봇", "자동화", "IoT", "빅데이터"
        ]
        
        print(f"🔍 IT/기술 키워드 {len(tech_keywords)}개로 뉴스 수집 중...")
        
        for keyword in tech_keywords:
            try:
                url = "https://api-v2.deepsearch.com/v1/articles"
                params = {
                    "api_key": DEEPSEARCH_API_KEY,
                    "q": keyword,
                    "limit": 10,
                    "start_date": start_date,
                    "end_date": end_date,
                    "sort": "published_at:desc"
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                for item in data.get("data", []):
                    pub_date = item.get("published_at", "")
                    if "T" in pub_date:
                        article_date = pub_date.split("T")[0]
                    else:
                        article_date = pub_date
                    
                    if start_date <= article_date <= end_date:
                        articles.append({
                            "id": f"news_{len(articles)}_{int(time.time())}",
                            "title": item.get("title", ""),
                            "content": item.get("summary", "") or item.get("content", ""),
                            "date": article_date,
                            "section": "IT/기술",
                            "keyword": keyword,
                            "url": item.get("content_url", "") or item.get("url", "")
                        })
                
                print(f"  ✅ '{keyword}': {len(data.get('data', []))}개 기사 수집")
                time.sleep(0.1)  # API 제한 방지
                
            except Exception as e:
                print(f"  ❌ '{keyword}' 오류: {e}")
                continue
        
        # 중복 제거
        unique_articles = []
        seen_titles = set()
        for article in articles:
            if article["title"] not in seen_titles:
                seen_titles.add(article["title"])
                unique_articles.append(article)
        
        print(f"✅ 총 {len(unique_articles)}개 고유 기사 수집 완료")
        return unique_articles
        
    except Exception as e:
        print(f"❌ 뉴스 수집 오류: {e}")
        return []

def upload_articles_to_azure_search(articles):
    """Azure AI Search에 기사 업로드"""
    try:
        search_client = SearchClient(
            endpoint=str(AZURE_SEARCH_ENDPOINT),
            index_name=str(AZURE_SEARCH_INDEX),
            credential=AzureKeyCredential(str(AZURE_SEARCH_API_KEY))
        )
        
        # 배치 업로드 (50개씩)
        batch_size = 50
        total_uploaded = 0
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]
            result = search_client.upload_documents(batch)
            
            success_count = len([r for r in result if r.succeeded])
            total_uploaded += success_count
            print(f"  📤 배치 {i//batch_size + 1}: {success_count}/{len(batch)}개 업로드 성공")
        
        print(f"✅ 총 {total_uploaded}개 기사 Azure AI Search 업로드 완료")
        return True
        
    except Exception as e:
        print(f"❌ Azure AI Search 업로드 오류: {e}")
        return False

def extract_keywords_with_gpt4o(articles):
    """Azure OpenAI GPT-4o로 키워드 추출"""
    try:
        # 기사 내용 합치기 (최대 50개 기사)
        articles_text = "\n".join([
            f"제목: {article['title']}\n내용: {article['content'][:200]}..."
            for article in articles[:50]
        ])
        
        prompt = f"""
다음 IT/기술 뉴스 기사들을 분석하고 가장 중요한 키워드들을 추출해주세요.

기사 내용:
{articles_text}

요구사항:
1. IT/기술 분야 핵심 키워드 위주로 추출
2. 구체적이고 의미있는 키워드만 선정
3. 각 키워드마다 예상 빈도도 함께 제공
4. 한국어로 응답
5. 응답 형식: 키워드1:빈도1, 키워드2:빈도2, ... (콤마로 구분)

키워드:
"""
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 IT/기술 뉴스 전문 키워드 분석가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        keywords_text = response.choices[0].message.content.strip()
        
        # 키워드:빈도 파싱
        keywords = []
        for item in keywords_text.split(','):
            if ':' in item:
                keyword, freq = item.strip().split(':', 1)
                try:
                    count = int(freq.strip())
                    keywords.append({"keyword": keyword.strip(), "count": count})
                except:
                    keywords.append({"keyword": keyword.strip(), "count": 10})
        
        print(f"✅ GPT-4o로 {len(keywords)}개 키워드 추출 완료")
        return keywords
        
    except Exception as e:
        print(f"❌ GPT-4o 키워드 추출 오류: {e}")
        return []

def analyze_keyword_frequency(keywords):
    """키워드 빈도 분석 및 정렬"""
    if not keywords:
        return []
    
    # 빈도 기준 정렬
    sorted_keywords = sorted(keywords, key=lambda x: x['count'], reverse=True)
    
    # 소스 정보 추가
    for kw in sorted_keywords:
        kw['source'] = 'IT기술'
    
    return sorted_keywords
        
    except Exception as e:
        print(f"❌ Error in get_weekly_hot_keywords_from_aggregation: {e}")
        # 오류 시 기본 날짜별 키워드 반환
        return [
            {"keyword": "월요일이슈", "count": 15000, "source": "날짜별"},
            {"keyword": "화요일이슈", "count": 14500, "source": "날짜별"},
            {"keyword": "수요일이슈", "count": 14000, "source": "날짜별"},
            {"keyword": "목요일이슈", "count": 13500, "source": "날짜별"},
            {"keyword": "금요일이슈", "count": 13000, "source": "날짜별"}
        ]

def get_aggregation_data(groupby, date_from, date_to, keyword=None, page_size=10):
    """DeepSearch API aggregation 호출"""
    
    if not DEEPSEARCH_API_KEY:
        return None
    
    url = "https://api-v2.deepsearch.com/v1/articles/aggregation"
    params = {
        "groupby": groupby,
        "date_from": date_from,
        "date_to": date_to,
        "page_size": page_size,
        "api_key": DEEPSEARCH_API_KEY
    }
    
    if keyword:
        params["keyword"] = keyword
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except Exception as e:
        log_error(
            error=e,
            file_name="main.py",
            function_name="get_aggregation_data",
            context=f"Aggregation API 호출 오류 - groupby: {groupby}, 기간: {date_from}~{date_to}",
            severity="MEDIUM"
        )
        return None

def get_current_week_news_from_deepsearch_global(query, start_date=None, end_date=None):
    if not DEEPSEARCH_API_KEY:
        print("DeepSearch API 키가 설정되지 않았습니다.")
        return []
    
    # 현재 주간 날짜 설정 (2025년 7월 3주차)
    if not start_date:
        start_date = "2025-07-14"  # 7월 3주차 시작
    if not end_date:
        end_date = "2025-07-20"    # 7월 3주차 종료
    
    try:
        # DeepSearch API 호출
        url = "https://api-v2.deepsearch.com/v1/global-articles"
        params = {
            "api_key": DEEPSEARCH_API_KEY,
            "q": query,
            "limit": 20,  # 가져올 뉴스 수
            "start_date": start_date,
            "end_date": end_date,
            "sort": "published_at:desc"  # 최신순 정렬
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        articles = []
        
        for item in data.get("data", []):
            # 날짜 필터링 (API에서 이미 필터링되지만 추가 확인)
            pub_date = item.get("published_at", "") or item.get("date", "")
            
            try:
                # ISO 형식 날짜 파싱
                if "T" in pub_date:
                    article_date = pub_date.split("T")[0]  # YYYY-MM-DD 형식으로 추출
                else:
                    article_date = pub_date
                
                # 지정된 주간 범위 내의 뉴스만 필터링
                if start_date <= article_date <= end_date:
                    articles.append({
                        "title": item.get("title", ""),
                        "description": item.get("summary", "") or (item.get("content", "") or "")[:200] + "...",
                        "link": item.get("url", "") or item.get("link", ""),
                        "pubDate": article_date
                    })
            except Exception as e:
                print(f"날짜 파싱 오류: {e}")
                # 날짜 파싱이 실패해도 기사는 포함시킴
                articles.append({
                    "title": item.get("title", ""),
                    "description": item.get("summary", "") or (item.get("content", "") or "")[:200] + "...",
                    "link": item.get("url", "") or item.get("link", ""),
                    "pubDate": pub_date
                })
                continue
        
        return articles[:10]  # 최대 10개 반환
        
    except Exception as e:
        log_error(
            error=e,
            file_name="main.py",
            function_name="get_current_week_news_from_deepsearch",
            context=f"DeepSearch API 호출 오류 - 쿼리: {query}, 기간: {start_date}~{end_date}",
            additional_info={
                "query": query,
                "start_date": start_date,
                "end_date": end_date,
                "has_api_key": bool(DEEPSEARCH_API_KEY)
            },
            severity="HIGH"
        )
        print(f"DeepSearch API 호출 오류: {e}")
        return []

# 정적 파일 서빙 추가
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def read_index():
    return FileResponse('index.html')

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
        log_error(
            error=e,
            file_name="main.py",
            function_name="get_weekly_summary",
            context="주간 요약 조회 중 오류 발생",
            additional_info={"search_filter": "id eq 'weekly_summary_2025_week3'"},
            severity="HIGH"
        )
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
        completion = openai_client.chat.completions.create(
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
    """산업별 키워드 분석 기반 동적 챗봇"""
    question = query.get("question", "")
    
    if not question:
        return {"answer": "질문을 입력해주세요."}
    
    # 1. 질문에서 키워드 추출 및 산업 분류
    keyword_info = extract_keyword_and_industry(question)
    
    # 2. 현재 주간 키워드 가져오기
    current_keywords = get_current_weekly_keywords()
    
    # 3. 질문 유형에 따른 동적 응답
    if keyword_info["type"] == "industry_analysis":
        # 산업별 분석 요청
        answer = generate_industry_based_answer(
            question, 
            keyword_info["keyword"], 
            keyword_info["industry"], 
            current_keywords
        )
    elif keyword_info["type"] == "keyword_trend":
        # 키워드 트렌드 분석 요청
        answer = generate_keyword_trend_answer(question, keyword_info["keyword"])
    elif keyword_info["type"] == "comparison":
        # 비교 분석 요청
        answer = generate_comparison_answer(question, keyword_info["keywords"])
    else:
        # 일반 질문 - 기존 방식 + 키워드 컨텍스트
        answer = generate_contextual_answer(question, current_keywords)
    
    return {"answer": answer}

def extract_keyword_and_industry(question):
    """질문에서 키워드와 산업 분류 추출"""
    import re
    
    # 산업 관련 키워드 매핑
    industry_keywords = {
        "사회": ["사회", "교육", "일자리", "복지", "정책", "제도", "시민", "공공"],
        "경제": ["경제", "시장", "투자", "금융", "주가", "비용", "수익", "매출", "기업"],
        "IT/과학": ["기술", "개발", "혁신", "연구", "과학", "IT", "소프트웨어", "하드웨어", "플랫폼"],
        "생활/문화": ["생활", "문화", "라이프스타일", "소비", "트렌드", "일상", "여가", "엔터테인먼트"],
        "세계": ["글로벌", "국제", "세계", "해외", "수출", "협력", "경쟁", "표준"]
    }
    
    question_lower = question.lower()
    
    # 산업 분류 추출
    detected_industry = None
    for industry, keywords in industry_keywords.items():
        if any(keyword in question_lower for keyword in keywords):
            detected_industry = industry
            break
    
    # 키워드 추출 (간단한 방식)
    # 현재 주간 키워드와 매치되는 것 찾기
    current_keywords = get_current_weekly_keywords()
    detected_keyword = None
    for keyword in current_keywords:
        if keyword in question or keyword.lower() in question_lower:
            detected_keyword = keyword
            break
    
    # 질문 유형 분류
    if detected_industry and detected_keyword:
        question_type = "industry_analysis"
    elif "vs" in question_lower or "비교" in question_lower or "차이" in question_lower:
        question_type = "comparison"
        # 비교 대상 키워드들 추출
        comparison_keywords = [kw for kw in current_keywords if kw.lower() in question_lower]
        return {
            "type": question_type,
            "keywords": comparison_keywords,
            "industry": detected_industry,
            "keyword": detected_keyword
        }
    elif detected_keyword:
        question_type = "keyword_trend"
    else:
        question_type = "general"
    
    return {
        "type": question_type,
        "keyword": detected_keyword,
        "industry": detected_industry or "사회"  # 기본값
    }

def get_current_weekly_keywords():
    """현재 주간 키워드 가져오기"""
    try:
        # Azure Search에서 모든 기사 가져오기
        results = search_client.search(search_text="*", top=50)
        
        # 모든 키워드 수집
        all_keywords = []
        for doc in results:
            content = doc.get("content", "")
            # "핵심 키워드: " 부분에서 키워드 추출
            if "핵심 키워드:" in content:
                keywords_text = content.split("핵심 키워드:")[1].split("\n")[0].strip()
                keywords = [k.strip() for k in keywords_text.split(",")]
                all_keywords.extend(keywords)
        
        # 키워드 빈도 계산 및 Top 3 선택
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        top_keywords = [keyword for keyword, count in keyword_counts.most_common(3)]
        
        return top_keywords if top_keywords else ["인공지능", "반도체", "기업"]
    except Exception as e:
        print(f"키워드 추출 오류: {e}")
        return ["인공지능", "반도체", "기업"]

def generate_industry_based_answer(question, keyword, industry, current_keywords):
    """산업별 키워드 분석 기반 답변 생성"""
    try:
        # 관련 기사 검색
        results = search_client.search(search_text=keyword, top=5)
        context = "\n".join([doc.get("content", "") for doc in results])
        
        # 산업별 관점 정의
        industry_context = {
            "사회": "사회적 영향, 정책적 측면, 시민 생활 변화",
            "경제": "경제적 파급효과, 시장 동향, 투자 관점",
            "IT/과학": "기술적 혁신, 연구개발 동향, 기술적 과제",
            "생활/문화": "일상생활 변화, 문화적 수용성, 소비자 행동",
            "세계": "글로벌 트렌드, 국제 경쟁, 해외 동향"
        }
        
        context_desc = industry_context.get(industry, "전반적인 관점")
        
        prompt = f"""
질문: {question}
키워드: {keyword}
관점: {industry} ({context_desc})
현재 주간 핵심 키워드: {', '.join(current_keywords)}

다음 뉴스 컨텍스트를 참고하여 {industry} 관점에서 답변해주세요:
{context}

답변 형식:
1. {industry} 관점에서 본 '{keyword}'의 현재 상황
2. 주요 동향과 변화
3. 전망과 시사점

구체적이고 전문적으로 답변해주세요.
"""
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"당신은 {industry} 분야의 전문가입니다. 뉴스 데이터를 바탕으로 {industry} 관점에서 키워드에 대해 분석하고 답변합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"죄송합니다. {industry} 관점에서의 '{keyword}' 분석 중 오류가 발생했습니다: {str(e)}"

def generate_keyword_trend_answer(question, keyword):
    """키워드 트렌드 분석 답변 생성"""
    try:
        # 키워드 관련 기사 검색
        results = search_client.search(search_text=keyword, top=8)
        articles = []
        for doc in results:
            content = doc.get("content", "")
            date = doc.get("date", "")
            if content:
                articles.append(f"[{date}] {content}")
        
        context = "\n".join(articles)
        
        prompt = f"""
질문: {question}
키워드: {keyword}

다음 뉴스 데이터를 바탕으로 '{keyword}'의 최근 트렌드를 분석해주세요:
{context}

분석 내용:
1. 최근 '{keyword}' 관련 주요 뉴스 동향
2. 시간적 변화와 발전 방향
3. 향후 전망과 관심 포인트

시간순으로 정리하여 트렌드를 명확하게 설명해주세요.
"""
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"당신은 '{keyword}' 분야의 트렌드 분석 전문가입니다. 뉴스 데이터를 바탕으로 시간적 변화와 동향을 분석합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"죄송합니다. '{keyword}' 트렌드 분석 중 오류가 발생했습니다: {str(e)}"

def generate_comparison_answer(question, keywords):
    """비교 분석 답변 생성"""
    try:
        # 각 키워드별로 관련 기사 검색
        comparison_data = {}
        for keyword in keywords:
            results = search_client.search(search_text=keyword, top=3)
            articles = [doc.get("content", "") for doc in results]
            comparison_data[keyword] = "\n".join(articles)
        
        context = ""
        for keyword, content in comparison_data.items():
            context += f"\n=== {keyword} 관련 뉴스 ===\n{content}\n"
        
        prompt = f"""
질문: {question}
비교 대상: {', '.join(keywords)}

다음 뉴스 데이터를 바탕으로 키워드들을 비교 분석해주세요:
{context}

비교 분석 내용:
1. 각 키워드의 현재 상황과 특징
2. 공통점과 차이점
3. 상호 관계와 영향
4. 각각의 전망과 중요성

객관적이고 균형잡힌 시각으로 비교해주세요.
"""
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"당신은 다양한 키워드를 비교 분석하는 전문가입니다. 뉴스 데이터를 바탕으로 객관적으로 비교 분석합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"죄송합니다. 키워드 비교 분석 중 오류가 발생했습니다: {str(e)}"

def generate_contextual_answer(question, current_keywords):
    """현재 키워드 컨텍스트 기반 일반 답변 생성"""
    try:
        # 질문과 관련된 기사 검색
        results = search_client.search(search_text=question, top=5)
        context = "\n".join([doc.get("content", "") for doc in results])
        
        # 현재 주간 키워드 컨텍스트 추가
        keywords_context = f"현재 주간 핵심 키워드: {', '.join(current_keywords)}"
        
        prompt = f"""
질문: {question}
{keywords_context}

다음 뉴스 데이터를 참고하여 질문에 답변해주세요:
{context}

답변 시 고려사항:
1. 현재 주간 핵심 키워드와의 연관성 언급
2. 구체적인 사례와 데이터 활용
3. 균형잡힌 시각으로 설명
4. 실용적인 정보 제공

명확하고 도움이 되는 답변을 제공해주세요.
"""
        prompt = f"""
질문: {question}
{keywords_context}

다음 뉴스 데이터를 참고하여 답변해주세요:
{context}

현재 주간 핵심 키워드들과 연관지어 답변하되, 질문의 맥락을 정확히 파악하여 답변해주세요.
"""
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"당신은 뉴스 분석 전문가입니다. 현재 주간 핵심 키워드({', '.join(current_keywords)})를 고려하여 질문에 답변합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"

def get_embedding(text):
    # Azure OpenAI text-embedding-ada-002로 임베딩 생성
    try:
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임베딩 생성 오류: {e}")

def generate_answer(question, context):
    # Azure OpenAI GPT-4o로 답변 생성
    try:
        completion = openai_client.chat.completions.create(
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
        
        response_data = {
            "keywords": top_keywords,
            "week_info": "7월 3주차 (2025.07.11~07.17) - AI 뉴스 분석"
        }
        return JSONResponse(content=response_data, media_type="application/json; charset=utf-8")
    except Exception as e:
        # 오류 시 샘플 데이터 반환
        response_data = {
            "keywords": ["인공지능", "반도체", "기업"],
            "week_info": "7월 3주차 (2025.07.11~07.17) - AI 뉴스 분석"
        }
        return JSONResponse(content=response_data, media_type="application/json; charset=utf-8")

@app.get("/weekly-keywords-by-date")
def get_weekly_keywords_by_date(start_date: str, end_date: str):
    """특정 날짜 범위의 주간 키워드 반환 (실제 aggregation 데이터 사용)"""
    try:
        # DeepSearch aggregation API로 실제 핫 키워드 추출
        hot_keywords = get_weekly_hot_keywords_from_aggregation(start_date, end_date)
        
        if hot_keywords:
            # 키워드와 카운트 정보를 포함하여 반환
            formatted_keywords = []
            for item in hot_keywords:
                if isinstance(item, dict):
                    keyword_with_count = f"{item['keyword']} ({item['count']:,}회)"
                    formatted_keywords.append(keyword_with_count)
                else:
                    # 기존 형식 호환성을 위해
                    formatted_keywords.append(str(item))
            
            return JSONResponse(content={
                "keywords": formatted_keywords,
                "week_info": f"{start_date} ~ {end_date} 주간 분석 (실제 데이터)",
                "article_count": sum(item['count'] if isinstance(item, dict) else 0 for item in hot_keywords)
            }, media_type="application/json; charset=utf-8")
        else:
            # Aggregation 실패시 기존 방식으로 폴백
            queries = ["AI", "인공지능", "기술", "경제", "사회", "정치", "IT", "스타트업", "투자"]
            all_articles = []
            
            for query in queries[:3]:  # API 호출 제한으로 3개만 사용
                articles = get_current_week_news_from_deepsearch(query, start_date, end_date)
                all_articles.extend(articles)
                
                # API 호출 간 딜레이
                import time
                time.sleep(0.1)
            
            if not all_articles:
                # 모든 API 실패시 해당 주간의 샘플 키워드 반환
                week_keywords = get_sample_keywords_by_date(start_date, end_date)
            return JSONResponse(content={
                "keywords": week_keywords,
                "week_info": f"{start_date} ~ {end_date} 주간 분석",
                "article_count": 0
            }, media_type="application/json; charset=utf-8")
        
        # 수집된 기사들에서 키워드 추출
        keywords = extract_keywords_from_articles(all_articles)
        
        response_data = {
            "keywords": keywords[:3],  # Top 3 키워드
            "week_info": f"{start_date} ~ {end_date} 주간 분석",
            "article_count": len(all_articles)
        }
        return JSONResponse(content=response_data, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        print(f"날짜별 키워드 추출 오류: {e}")
        # 오류 시 해당 주간의 샘플 키워드 반환
        week_keywords = get_sample_keywords_by_date(start_date, end_date)
        return JSONResponse(content={
            "keywords": week_keywords,
            "week_info": f"{start_date} ~ {end_date} 주간 분석",
            "article_count": 0
        }, media_type="application/json; charset=utf-8")

def get_sample_keywords_by_date(start_date: str, end_date: str):
    """날짜에 따른 샘플 키워드 반환"""
    if "07-01" in start_date:  # 7월 1주차
        return ["전기차", "배터리", "충전인프라"]
    elif "07-06" in start_date:  # 7월 2주차  
        return ["메타버스", "VR", "가상현실"]
    elif "07-14" in start_date:  # 7월 3주차
        return ["정보통신산업진흥원", "AI Youth Festa 2025", "인공지능"]
    else:
        return ["기술", "혁신", "디지털"]

def extract_keywords_from_articles(articles):
    """기사들에서 키워드 추출"""
    try:
        # 모든 기사의 제목과 설명을 합쳐서 텍스트 생성
        all_text = ""
        for article in articles:
            all_text += f"{article.get('title', '')} {article.get('description', '')} "
        
        if not all_text.strip():
            return ["키워드1", "키워드2", "키워드3"]
        
        # OpenAI를 사용하여 키워드 추출
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 뉴스 기사에서 핵심 키워드를 추출하는 AI입니다. 주어진 뉴스 텍스트에서 가장 중요하고 핵심적인 키워드 3개를 추출해주세요."
                },
                {
                    "role": "user",
                    "content": f"다음 뉴스 텍스트에서 핵심 키워드 3개를 추출해주세요. 키워드는 콤마로 구분하여 응답해주세요:\n\n{all_text[:2000]}"  # 텍스트 길이 제한
                }
            ],
            max_tokens=100,
            temperature=0.3
        )
        
        keywords_text = response.choices[0].message.content
        if keywords_text:
            keywords_text = keywords_text.strip()
            keywords = [k.strip() for k in keywords_text.split(",")]
        else:
            keywords = ["키워드1", "키워드2", "키워드3"]
        
        return keywords[:3] if len(keywords) >= 3 else keywords + ["기술", "뉴스", "트렌드"][:3-len(keywords)]
        
    except Exception as e:
        print(f"키워드 추출 오류: {e}")
        return ["AI", "기술", "혁신"]

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
def get_keyword_articles(keyword: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """키워드 관련 기사 Top 5 조회 (DeepSearch API 사용)"""
    try:
        # 키워드에서 "(n회)" 형태의 텍스트 제거
        import re
        clean_keyword = re.sub(r'\s*\(\d+[,\d]*회\)', '', keyword).strip()
        
        print(f"🔍 키워드 기사 조회 - 원본: {keyword}, 정리된 키워드: {clean_keyword}")
        print(f"📅 날짜 범위: {start_date} ~ {end_date}")
        
        # 날짜 범위가 제공되면 해당 날짜 범위로 검색
        if start_date and end_date:
            deepsearch_articles = get_current_week_news_from_deepsearch(clean_keyword, start_date, end_date)
        else:
            # 기본값: 현재 주차 (3주차)
            deepsearch_articles = get_current_week_news_from_deepsearch(clean_keyword, "2025-07-14", "2025-07-18")
        
        print(f"📰 DeepSearch 검색 결과: {len(deepsearch_articles)}개 기사")
        
        if deepsearch_articles:
            # DeepSearch API 결과를 사용
            articles = []
            for article in deepsearch_articles[:5]:  # Top 5만 선택
                print(f"  - 제목: {article['title'][:50]}...")
                print(f"    URL: {article['link']}")
                articles.append({
                    "title": article["title"],
                    "summary": article["description"],
                    "date": article["pubDate"],
                    "url": article["link"]
                })
            
            print(f"✅ DeepSearch API로 {len(articles)}개 기사 반환")
            return {"articles": articles}
        
        # DeepSearch API 결과가 없으면 Azure Search 사용
        print("🔍 DeepSearch 결과가 없어 Azure Search 사용")
        results = search_client.search(
            search_text=clean_keyword,
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
                    "date": date,
                    "url": "#"  # Azure Search에는 URL이 없으므로 기본값
                })
        
        print(f"📋 Azure Search 결과: {len(articles)}개 기사")
        
        if not articles:
            print("❌ 모든 소스에서 기사를 찾을 수 없음")
            
            # 더 친화적인 메시지와 대안 제안
            suggestions = []
            
            # 기본 키워드 제안
            if clean_keyword.lower() in ["db", "디비"]:
                suggestions = ["DB금융투자", "DB손해보험", "DB그룹", "삼성전자", "네이버"]
            elif clean_keyword.lower() in ["ai", "인공지능"]:
                suggestions = ["ChatGPT", "삼성전자", "네이버", "SKT", "LG전자"]
            else:
                suggestions = ["삼성전자", "네이버", "AI", "반도체", "5G"]
            
            return {
                "articles": [], 
                "message": f"'{clean_keyword}' 키워드 관련 기사를 찾을 수 없습니다.",
                "suggestions": {
                    "reason": "해당 기간(2025-07-14 ~ 2025-07-18)에 관련 뉴스가 없거나 검색어가 너무 구체적일 수 있습니다.",
                    "alternatives": suggestions,
                    "tip": "더 일반적인 키워드나 관련 기업명으로 검색해보세요."
                }
            }
        
        return {"articles": articles}
        
    except Exception as e:
        print(f"❌ 키워드 기사 조회 오류: {e}")
        return {"error": f"기사 조회 중 오류가 발생했습니다: {str(e)}"}

@app.post("/keyword-analysis")
def analyze_keyword_dynamically(request: dict):
    """동적 키워드 분석 - 클릭된 키워드에 대한 다각도 분석"""
    keyword = request.get("keyword", "")
    
    if not keyword:
        return {"error": "키워드가 필요합니다."}
    
    try:
        # 1. 키워드 관련 뉴스 검색
        search_results = search_client.search(
            search_text=keyword,
            top=10,
            select=["title", "content", "date"]  # 실제 존재하는 필드만 선택
        )
        
        # 2. 검색된 뉴스들을 컨텍스트로 활용
        context_articles = []
        for doc in search_results:
            if len(context_articles) >= 5:
                break
            context_articles.append({
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "date": doc.get("date", ""),
                "section": "AI/기술"  # 기본값 설정
            })
        
        # 3. 다각도 분석 생성
        perspectives = [
            "사회적 영향",
            "경제적 측면", 
            "기술적 혁신",
            "미래 전망",
            "주요 이슈"
        ]
        
        analyses = {}
        
        for perspective in perspectives:
            analysis_text = generate_perspective_analysis(keyword, perspective, context_articles)
            analyses[perspective] = analysis_text
        
        # 4. 키워드 트렌드 요약
        trend_summary = generate_keyword_trend_summary(keyword, context_articles)
        
        return {
            "keyword": keyword,
            "trend_summary": trend_summary,
            "perspectives": analyses,
            "related_articles": context_articles
        }
        
    except Exception as e:
        log_error(
            error=e,
            file_name="main.py",
            function_name="analyze_keyword_dynamically",
            context=f"키워드 분석 중 오류 발생 - 키워드: {keyword}",
            additional_info={
                "keyword": keyword,
                "search_attempted": True
            },
            severity="HIGH"
        )
        return {"error": f"분석 생성 중 오류가 발생했습니다: {str(e)}"}

def generate_perspective_analysis(keyword, perspective, articles):
    """특정 관점에서의 키워드 분석 생성"""
    try:
        # 관련 기사들의 내용을 컨텍스트로 구성
        context = "\n".join([
            f"제목: {article['title']}\n내용: {article['content'][:200]}..."
            for article in articles[:3]
        ])
        
        prompt = f"""
다음 키워드에 대해 {perspective} 관점에서 분석해주세요:

키워드: {keyword}

관련 뉴스:
{context}

분석 요구사항:
- {perspective} 관점에서 해당 키워드의 의미와 중요성
- 현재 트렌드와 향후 전망
- 핵심 포인트 3가지
- 간결하고 명확한 설명 (200자 이내)

분석 결과를 한국어로 작성해주세요.
"""
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 뉴스 분석 전문가입니다. 주어진 키워드를 특정 관점에서 깊이 있게 분석하고, 핵심 인사이트를 제공합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"분석 생성 중 오류가 발생했습니다: {str(e)}"

def generate_keyword_trend_summary(keyword, articles):
    """키워드 트렌드 요약 생성"""
    try:
        context = "\n".join([
            f"제목: {article['title']}\n내용: {article['content'][:150]}..."
            for article in articles[:5]
        ])
        
        prompt = f"""
다음 키워드의 현재 트렌드를 요약해주세요:

키워드: {keyword}

관련 뉴스:
{context}

요약 요구사항:
- 현재 이슈의 핵심 내용
- 주요 이해관계자들
- 사회적/경제적 영향
- 한 문장으로 핵심 메시지 요약

150자 이내로 간결하게 작성해주세요.
"""
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 뉴스 트렌드 분석 전문가입니다. 복잡한 이슈를 핵심만 간추려 명확하게 설명합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=200
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"키워드 '{keyword}'에 대한 트렌드 분석을 생성할 수 없습니다."
        
        if not articles:
            # 샘플 데이터 반환
            articles = [
                {
                    "title": f"'{keyword}' 관련 뉴스 1",
                    "summary": f"{keyword}에 대한 최신 동향과 관련된 주요 내용을 다룬 기사입니다.",
                    "date": "2025-07-17",
                    "url": "https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=105&oid=001&aid=0014567890"
                },
                {
                    "title": f"'{keyword}' 관련 뉴스 2", 
                    "summary": f"{keyword} 분야의 새로운 발전과 전망에 대해 분석한 기사입니다.",
                    "date": "2025-07-16",
                    "url": "https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=105&oid=001&aid=0014567891"
                },
                {
                    "title": f"'{keyword}' 관련 뉴스 3",
                    "summary": f"{keyword} 산업의 미래 전망과 기술 혁신 동향을 분석한 기사입니다.",
                    "date": "2025-07-15",
                    "url": "https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=105&oid=001&aid=0014567892"
                },
                {
                    "title": f"'{keyword}' 관련 뉴스 4",
                    "summary": f"{keyword} 분야의 최신 연구 결과와 시장 동향을 다룬 기사입니다.",
                    "date": "2025-07-14",
                    "url": "https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=105&oid=001&aid=0014567893"
                },
                {
                    "title": f"'{keyword}' 관련 뉴스 5",
                    "summary": f"{keyword} 기술의 실용화와 상용화 계획에 대한 기사입니다.",
                    "date": "2025-07-13",
                    "url": "https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=105&oid=001&aid=0014567894"
                }
            ]
        
        return {"articles": articles}
    except Exception as e:
        log_error(
            error=e,
            file_name="main.py",
            function_name="get_keyword_articles",
            context=f"키워드 기사 검색 오류 - 키워드: {keyword}",
            additional_info={"keyword": keyword},
            severity="MEDIUM"
        )
        print(f"키워드 기사 검색 오류: {e}")
        return {
            "articles": [
                {
                    "title": "검색 오류",
                    "summary": f"'{keyword}' 관련 기사를 불러오는 중 오류가 발생했습니다.",
                    "date": "오류",
                    "url": ""
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
        
        completion = openai_client.chat.completions.create(
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
