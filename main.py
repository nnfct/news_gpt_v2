# News GPT v2 - 새로운 구조 (DeepSearch 기반 워크플로우)
import os
import re
import time
import logging
import requests
import hashlib
import uvicorn
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from dotenv import load_dotenv
from openai import AzureOpenAI
from functools import wraps

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("news_gpt_v2")

# 환경변수 로드
load_dotenv()

# FastAPI 앱 인스턴스 생성
app = FastAPI(title="News GPT v2", description="AI 뉴스 키워드 분석 플랫폼")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 환경변수 로드
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
DEEPSEARCH_API_KEY = os.getenv("DEEPSEARCH_API_KEY")

# Azure OpenAI 클라이언트 초기화
openai_client = AzureOpenAI(
    api_key=str(AZURE_OPENAI_API_KEY),
    api_version="2024-02-15-preview",
    azure_endpoint=str(AZURE_OPENAI_ENDPOINT)
)

# DeepSearch API URLs (국내 + 해외)
DEEPSEARCH_TECH_URL = "https://api-v2.deepsearch.com/v1/articles/tech"
DEEPSEARCH_KEYWORD_URL = "https://api-v2.deepsearch.com/v1/articles"
DEEPSEARCH_GLOBAL_TECH_URL = "https://api-v2.deepsearch.com/v1/global-articles"
DEEPSEARCH_GLOBAL_KEYWORD_URL = "https://api-v2.deepsearch.com/v1/global-articles"


# API 호출 재시도 데코레이터 (성능 최적화)
def retry_on_exception(max_retries=1, delay=0.1, backoff=1.2, allowed_exceptions=(Exception,)):  # 빠른 재시도
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while True:
                try:
                    return func(*args, **kwargs)
                except allowed_exceptions as e:
                    retries += 1
                    logger.warning(f"{func.__name__} 실패({retries}/{max_retries}): {e}")
                    if retries >= max_retries:
                        logger.error(f"{func.__name__} 최대 재시도 초과: {e}")
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator

# =============================================================================
# 새로운 워크플로우 API 엔드포인트들
# =============================================================================

@app.get("/")
async def serve_home():
    """메인 페이지 제공"""
    return FileResponse("index.html")

# 1단계: Tech 기사에서 키워드 추출 (프론트와 연동)
@app.get("/api/keywords")
async def get_weekly_keywords(start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"), 
                            end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")):
    """새로운 워크플로우: Tech 기사 → GPT 키워드 추출 → 키워드별 기사 검색 (Azure AI Search 제거)"""
    try:
        logger.info(f"🚀 새로운 워크플로우 시작 - 기간: {start_date} ~ {end_date}")
        
        # 1단계: DeepSearch Tech에서 기사 수집 (날짜 포함)
        tech_articles = await fetch_tech_articles(start_date, end_date)
        if not tech_articles:
            return {"error": "Tech 기사를 찾을 수 없습니다", "keywords": [], "articles_count": 0}
        
        # 2단계: GPT로 키워드 추출 (Azure AI Search 건너뛰기)
        extracted_keywords = await extract_keywords_with_gpt(tech_articles)
        if not extracted_keywords:
            return {"error": "키워드 추출 실패", "keywords": [], "articles_count": len(tech_articles)}
        
        # 3단계: 추출된 키워드들을 메모리에 저장 (관련 기사 검색용)
        store_keywords_in_memory(extracted_keywords, start_date, end_date)
        
        return {
            "keywords": extracted_keywords,
            "date_range": f"{start_date} ~ {end_date}",
            "tech_articles_count": len(tech_articles),
            "workflow": "Tech기사 → GPT키워드추출 (Azure AI Search 제거)",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"워크플로우 오류: {e}", exc_info=True)
        return {"error": str(e), "keywords": [], "articles_count": 0}

# 4단계: 키워드 클릭시 관련 기사 노출
@app.get("/api/keyword-articles/{keyword}")
async def get_keyword_articles(keyword: str, 
                              start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
                              end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")):
    """키워드 클릭시 관련 기사들을 반환"""
    try:
        logger.info(f"🔍 키워드 '{keyword}' 관련 기사 검색 - 기간: {start_date} ~ {end_date}")
        
        # DeepSearch 키워드 검색으로 관련 기사 찾기
        articles = await search_articles_by_keyword(keyword, start_date, end_date)
        
        return {
            "keyword": keyword,
            "articles": articles,
            "total_count": len(articles),
            "date_range": f"{start_date} ~ {end_date}",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"키워드 '{keyword}' 기사 검색 오류: {e}", exc_info=True)
        return {"error": str(e), "keyword": keyword, "articles": [], "total_count": 0}

# 5단계: 기사 클릭시 원본 URL로 리다이렉트
@app.get("/api/redirect/{article_id}")
async def redirect_to_original(article_id: str):
    """기사 클릭시 원본 URL로 리다이렉트"""
    try:
        # 메모리나 캐시에서 article_id로 원본 URL 찾기
        original_url = get_original_url_by_id(article_id)
        
        if original_url:
            logger.info(f"🔗 기사 리다이렉트: {article_id} → {original_url}")
            return RedirectResponse(url=original_url, status_code=302)
        else:
            raise HTTPException(status_code=404, detail=f"기사 ID '{article_id}'를 찾을 수 없습니다")
            
    except Exception as e:
        logger.error(f"리다이렉트 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 기존 호환성을 위한 엔드포인트 (deprecated)
@app.get("/keyword-articles")
async def get_keyword_articles_legacy(
    keyword: str = Query(..., description="검색할 키워드"),
    start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")
):
    """레거시 키워드 기반 관련 기사 검색 API (호환성용)"""
    try:
        articles = await search_articles_by_keyword(keyword, start_date, end_date)
        return {
            "keyword": keyword,
            "total": len(articles),
            "articles": articles,
            "period": f"{start_date} ~ {end_date}",
            "status": "success",
            "note": "이 엔드포인트는 deprecated됩니다. /api/keyword-articles/{keyword}를 사용하세요."
        }
    except Exception as e:
        logger.error(f"/keyword-articles 오류: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={
            "error": str(e),
            "keyword": keyword,
            "articles": [],
            "total": 0
        })

@app.get("/api/global-keyword-articles/{keyword}")
async def get_global_keyword_articles(
    keyword: str, 
    start_date: str = Query("2025-07-14", description="시작일"),
    end_date: str = Query("2025-07-18", description="종료일")
):
    """해외 키워드별 관련 기사 검색 API"""
    try:
        logger.info(f"🌍 해외 키워드별 기사 검색: '{keyword}' ({start_date} ~ {end_date})")
        
        # 해외 키워드 검색 실행
        articles = await search_global_keyword_articles(keyword, start_date, end_date)
        
        # 응답 데이터 구성
        response_data = {
            "keyword": keyword,
            "articles": articles,
            "total": len(articles),
            "date_range": f"{start_date} ~ {end_date}",
            "region": "global",
            "status": "success"
        }
        
        return JSONResponse(content=response_data, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        logger.error(f"❌ 해외 키워드별 기사 검색 오류: {e}")
        return JSONResponse(status_code=500, content={
            "error": str(e),
            "keyword": keyword,
            "articles": [],
            "total": 0,
            "region": "global"
        })

# =============================================================================
# 새로운 워크플로우 핵심 함수들
# =============================================================================

# 메모리 저장소 (실제 운영에서는 Redis나 데이터베이스 사용 권장)
articles_cache = {}  # {article_id: {url, title, content, ...}}
keywords_cache = {}  # {keyword: [article_ids]}

# 1단계: DeepSearch Tech에서 기사 수집
@retry_on_exception(max_retries=1, delay=0.1, backoff=1.5, allowed_exceptions=(requests.RequestException,))
async def fetch_tech_articles(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """DeepSearch Tech 카테고리에서 기사들을 수집합니다 (빠른 처리)"""
    if not DEEPSEARCH_API_KEY:
        logger.error("❌ DeepSearch API 키가 설정되지 않음")
        return []
    
    try:
        # 빠른 처리를 위해 최소한의 기사만 수집
        base_url = DEEPSEARCH_TECH_URL
        params = {
            "api_key": DEEPSEARCH_API_KEY,
            "date_from": start_date,
            "date_to": end_date,
            "page_size": 20  # 20개로 줄여서 빠른 처리
        }
        
        logger.info(f"� Tech 기사 수집 중...")
        response = requests.get(base_url, params=params, timeout=5)  # 5초로 단축
        logger.info(f"� 응답 상태: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ API 호출 실패: {response.status_code}")
            return []
            
        response.raise_for_status()
        data = response.json()
        
        # 응답 구조 확인 및 기사 추출
        articles = []
        if "articles" in data:
            articles = data["articles"]
        elif "data" in data:
            articles = data["data"]
        else:
            logger.warning(f"알 수 없는 응답 구조: {list(data.keys())}")
            return []
        
        # 기사 정규화 및 ID 생성
        processed_articles = []
        for article in articles:
            article_id = generate_article_id(article)
            
            # 날짜 정보 처리 개선
            published_at = article.get("published_at", "")
            formatted_date = "날짜 정보 없음"
            if published_at:
                try:
                    if "T" in published_at:
                        formatted_date = published_at.split("T")[0]  # YYYY-MM-DD
                    else:
                        formatted_date = published_at[:10]  # 처음 10자리만
                except:
                    formatted_date = "날짜 정보 없음"
            
            processed_article = {
                "id": article_id,
                "title": article.get("title", "제목 없음"),
                "content": article.get("summary", "") or article.get("content", ""),
                "summary": (article.get("summary", "") or article.get("content", ""))[:150] + "..." if article.get("summary") or article.get("content") else "요약 정보 없음",
                "url": article.get("url", "") or article.get("content_url", ""),
                "date": formatted_date,
                "published_at": published_at,
                "source": article.get("source", ""),
                "category": "tech"
            }
            
            # 캐시에 저장 (URL 리다이렉트용)
            articles_cache[article_id] = processed_article
            processed_articles.append(processed_article)
        
        logger.info(f"✅ Tech 기사 {len(processed_articles)}개 수집 완료")
        return processed_articles
        
    except Exception as e:
        logger.error(f"❌ Tech 기사 수집 오류: {e}", exc_info=True)
        return []

# 1-2단계: 해외 Tech 기사 수집 (Global)
@retry_on_exception(max_retries=1, delay=0.1, backoff=1.5, allowed_exceptions=(requests.RequestException,))
async def fetch_global_tech_articles(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """DeepSearch Global API에서 해외 Tech 기사들을 수집합니다 (빠른 처리)"""
    if not DEEPSEARCH_API_KEY:
        logger.error("❌ DeepSearch API 키가 설정되지 않음")
        return []
    
    try:
        # 해외 Tech 기사 수집을 위한 URL 구성
        base_url = DEEPSEARCH_GLOBAL_TECH_URL
        params = {
            "api_key": DEEPSEARCH_API_KEY,
            "keyword": "tech",  # 해외에서는 tech 키워드로 검색
            "date_from": start_date,
            "date_to": end_date,
            "page_size": 20  # 빠른 처리를 위해 20개로 제한
        }
        
        logger.info(f"🌍 해외 Tech 기사 수집 중...")
        response = requests.get(base_url, params=params, timeout=5)  # 5초 타임아웃
        logger.info(f"📊 해외 응답 상태: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ 해외 API 호출 실패: {response.status_code}")
            return []
            
        response.raise_for_status()
        data = response.json()
        
        # 응답 구조 확인 및 기사 추출
        articles = []
        if 'data' in data:
            articles = data['data']
        elif 'articles' in data:
            articles = data['articles']
        elif isinstance(data, list):
            articles = data
        else:
            logger.warning(f"알 수 없는 해외 응답 구조: {list(data.keys())}")
            return []
        
        # 기사 정규화 및 ID 생성
        processed_articles = []
        for article in articles:
            article_id = generate_article_id(article)
            
            # 날짜 정보 처리 개선
            published_at = article.get("published_at", "")
            formatted_date = "날짜 정보 없음"
            if published_at:
                try:
                    if "T" in published_at:
                        formatted_date = published_at.split("T")[0]  # YYYY-MM-DD
                    else:
                        formatted_date = published_at[:10]  # 처음 10자리만
                except:
                    formatted_date = "날짜 정보 없음"
            
            processed_article = {
                "id": article_id,
                "title": article.get("title", "제목 없음"),
                "content": article.get("summary", "") or article.get("content", "내용 없음"),
                "url": article.get("content_url", "") or article.get("url", ""),
                "date": formatted_date,
                "source": "해외",
                "category": "global_tech"
            }
            
            # 캐시에 저장 (URL 리다이렉트용)
            articles_cache[article_id] = processed_article
            processed_articles.append(processed_article)
        
        logger.info(f"✅ 해외 Tech 기사 {len(processed_articles)}개 수집 완료")
        return processed_articles
        
    except Exception as e:
        logger.error(f"❌ 해외 Tech 기사 수집 오류: {e}", exc_info=True)
        return []

# 2단계: GPT로 키워드 추출
async def extract_keywords_with_gpt(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """GPT를 사용해 기사들에서 키워드를 추출합니다 (최적화됨)"""
    if not articles:
        logger.warning("❌ 분석할 기사가 없습니다")
        return []
    
    try:
        # 최적화: 상위 10개 기사만 분석하고 제목만 사용
        top_articles = articles[:10]
        titles_text = " ".join([article['title'][:50] for article in top_articles])
        
        # 간단한 프롬프트로 속도 향상
        prompt = f"""다음 IT기술 뉴스 제목에서 핵심 키워드 3개만 추출하세요:
{titles_text}

형식: 키워드1, 키워드2, 키워드3"""
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "IT기술 키워드 추출 전문가"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,  # 더 짧게
            temperature=0  # 일관성 최대화
        )
        
        
        keywords_text = response.choices[0].message.content or ""
        logger.info(f"🚀 GPT 키워드 추출 완료: {keywords_text}")
        
        # 빠른 키워드 파싱
        keywords = []
        for i, item in enumerate(keywords_text.split(',')[:3], 1):  # 최대 3개
            keyword = item.strip().replace('.', '').replace('1', '').replace('2', '').replace('3', '')
            keyword = re.sub(r'[^\w가-힣]', '', keyword)  # 특수문자 제거
            
            if keyword and 2 <= len(keyword) <= 10:
                keywords.append({
                    "keyword": keyword,
                    "count": 30 - (i * 5),
                    "rank": i
                })
        
        # 기본 키워드 (빈 결과 시)
        if not keywords:
            keywords = [
                {"keyword": "인공지능", "count": 25, "rank": 1},
                {"keyword": "반도체", "count": 20, "rank": 2},
                {"keyword": "클라우드", "count": 15, "rank": 3}
            ]
        
        return keywords[:3]  # 최대 3개 반환
        
    except Exception as e:
        logger.error(f"❌ 키워드 추출 오류: {e}")
        return [
            {"keyword": "인공지능", "count": 25, "rank": 1},
            {"keyword": "반도체", "count": 20, "rank": 2},
            {"keyword": "클라우드", "count": 15, "rank": 3}
        ]

# 3단계: 키워드를 메모리에 저장
def store_keywords_in_memory(keywords: List[Dict[str, Any]], start_date: str, end_date: str):
    """추출된 키워드들을 메모리에 저장합니다"""
    for keyword_data in keywords:
        keyword = keyword_data['keyword']
        keywords_cache[keyword] = {
            "keyword_data": keyword_data,
            "date_range": f"{start_date}~{end_date}",
            "cached_at": time.time()
        }
    logger.info(f"📝 {len(keywords)}개 키워드를 메모리에 저장 완료")

# 4단계: 키워드로 관련 기사 검색
@retry_on_exception(max_retries=3, delay=0.5, backoff=2, allowed_exceptions=(requests.RequestException,))
async def search_articles_by_keyword(keyword: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """특정 키워드로 DeepSearch에서 관련 기사들을 검색합니다"""
    if not DEEPSEARCH_API_KEY:
        logger.error("❌ DeepSearch API 키가 설정되지 않음")
        return []
    
    try:
        # 사용자 제공 예시 URL 구조 사용
        base_url = DEEPSEARCH_KEYWORD_URL
        params = {
            "api_key": DEEPSEARCH_API_KEY,
            "keyword": keyword,  # 사용자 예시에 맞춰 keyword 파라미터 사용
            "date_from": start_date,
            "date_to": end_date,
            "page_size": 15  # 기사 수를 줄여서 빠른 응답
        }
        
        logger.info(f"🔍 키워드 '{keyword}' 기사 검색 중... URL: {base_url}")
        logger.info(f"🔍 파라미터: {params}")
        response = requests.get(base_url, params=params, timeout=3)  # 3초로 단축
        logger.info(f"🔍 응답 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ 키워드 검색 API 호출 실패: {response.status_code}")
            logger.error(f"❌ 응답 내용: {response.text}")
            return []
            
        response.raise_for_status()
        data = response.json()
        
        # 응답 구조 확인 및 기사 추출
        articles = []
        if "articles" in data:
            articles = data["articles"]
        elif "data" in data:
            articles = data["data"]
        else:
            logger.warning(f"알 수 없는 키워드 검색 응답 구조: {list(data.keys())}")
            return []
        
        # 기사 정규화 및 캐시 저장
        processed_articles = []
        for article in articles:
            article_id = generate_article_id(article)
            
            # 날짜 정보 처리 개선
            published_at = article.get("published_at", "")
            formatted_date = "날짜 정보 없음"
            if published_at:
                try:
                    if "T" in published_at:
                        formatted_date = published_at.split("T")[0]  # YYYY-MM-DD
                    else:
                        formatted_date = published_at[:10]  # 처음 10자리만
                except:
                    formatted_date = "날짜 정보 없음"
            
            processed_article = {
                "id": article_id,
                "title": article.get("title", "제목 없음"),
                "summary": (article.get("summary", "") or article.get("content", ""))[:150] + "..." if article.get("summary") or article.get("content") else "요약 정보 없음",
                "content": article.get("summary", "") or article.get("content", ""),
                "url": article.get("url", "") or article.get("content_url", ""),
                "date": formatted_date,
                "published_at": published_at,
                "source": article.get("source", ""),
                "keyword": keyword,
                "relevance_score": calculate_relevance_score(article, keyword)
            }
            
            # 캐시에 저장 (URL 리다이렉트용)
            articles_cache[article_id] = processed_article
            processed_articles.append(processed_article)
        
        # 관련성 점수 기준으로 정렬
        processed_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"✅ 키워드 '{keyword}' 관련 기사 {len(processed_articles)}개 검색 완료")
        return processed_articles[:15]  # 상위 15개만 반환
        
    except Exception as e:
        logger.error(f"❌ 키워드 '{keyword}' 검색 오류: {e}", exc_info=True)
        return []

# 5단계: 기사 ID로 원본 URL 찾기
def get_original_url_by_id(article_id: str) -> Optional[str]:
    """기사 ID로 원본 URL을 찾습니다"""
    article = articles_cache.get(article_id)
    if article:
        return article.get("url")
    return None

# =============================================================================
# 유틸리티 함수들
# =============================================================================

def generate_article_id(article: Dict[str, Any]) -> str:
    """기사 정보로 고유 ID를 생성합니다"""
    content = f"{article.get('title', '')}{article.get('url', '')}{article.get('published_at', '')}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]

def calculate_relevance_score(article: Dict[str, Any], keyword: str) -> float:
    """기사와 키워드의 관련성 점수를 계산합니다"""
    title = article.get("title", "").lower()
    content = article.get("summary", "") or article.get("content", "")
    content = content.lower()
    keyword_lower = keyword.lower()
    
    score = 0.0
    
    # 제목에 키워드 포함시 높은 점수
    if keyword_lower in title:
        score += 10.0
    
    # 내용에 키워드 포함시 점수 추가
    content_count = content.count(keyword_lower)
    score += content_count * 2.0
    
    # 최근 기사일수록 높은 점수
    pub_date = article.get("published_at", "")
    if "2025-07" in pub_date:
        score += 5.0
    
    return score

# 기존 함수들을 새로운 워크플로우에 맞게 수정...
async def search_keyword_articles(keyword: str, start_date: str = "2025-07-14", end_date: str = "2025-07-18"):
    """특정 키워드로 기사 검색 (더 정확한 검색, 한국어 우선, 날짜 필터링)"""
    if not DEEPSEARCH_API_KEY:
        logger.error("❌ DeepSearch API 키 없음")
        return []
    try:
        # IT 키워드에 대해서만 정확한 검색
        if keyword == "IT":
            search_terms = ["IT", "정보기술", "Information Technology"]
        else:
            search_terms = [keyword]
        articles = []
        for search_term in search_terms:
            try:
                # DeepSearch API에서 경제,기술 카테고리 + 키워드 검색
                url = f"https://api-v2.deepsearch.com/v1/articles/economy,tech"
                params = {
                    "api_key": DEEPSEARCH_API_KEY,
                    "date_from": start_date,
                    "date_to": end_date,
                    "q": search_term  # 키워드 검색 추가
                }
                response = requests.get(url, params=params, timeout=5)
                response.raise_for_status()
                data = response.json()
                for item in data.get("data", []):
                    pub_date = item.get("published_at", "")
                    if "T" in pub_date:
                        article_date = pub_date.split("T")[0]
                    else:
                        article_date = pub_date
                    if article_date:
                        title = item.get("title", "")
                        content = item.get("summary", "") or item.get("content", "")
                        # 관련성 점수 계산(간단화)
                        relevance_score = 1.0 if keyword in title or keyword in content else 0.5
                        korean_chars = len([c for c in title + content if ord(c) >= 0xAC00 and ord(c) <= 0xD7A3])
                        total_chars = len(title + content)
                        is_korean = korean_chars / max(total_chars, 1) > 0.3
                        articles.append({
                            "title": title,
                            "content": content,
                            "source_url": item.get("content_url", "") or item.get("url", ""),
                            "date": article_date,
                            "relevance_score": relevance_score,
                            "search_term": search_term,
                            "is_korean": is_korean
                        })
            except Exception as e:
                logger.warning(f"❌ '{search_term}' 검색 오류: {e}")
                continue
        # 중복 제거 (제목 기준)
        unique_articles = []
        seen_titles = set()
        for article in articles:
            title = article.get("title", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)
        # 한국어 기사 우선 + 관련성 점수 기반 정렬
        unique_articles.sort(key=lambda x: (
            not x.get("is_korean", False),
            -x.get("relevance_score", 0),
            x.get("date", "")
        ))
        logger.info(f"✅ '{keyword}' ({start_date}~{end_date}): {len(unique_articles)}개 관련 기사 검색 완료 (한국어 우선, 관련성 필터링)")
        return unique_articles[:12]
    except Exception as e:
        logger.error(f"❌ '{keyword}' 검색 오류: {e}")
        return []

# 해외 키워드별 기사 검색 함수
async def search_global_keyword_articles(keyword: str, start_date: str = "2025-07-14", end_date: str = "2025-07-18"):
    """해외 키워드로 DeepSearch Global API에서 관련 기사 검색"""
    try:
        logger.info(f"🌍 해외 키워드 '{keyword}' 기사 검색 중...")
        
        # 해외 키워드 검색 (GPT 추출된 키워드 사용)
        base_url = DEEPSEARCH_GLOBAL_KEYWORD_URL
        params = {
            "api_key": DEEPSEARCH_API_KEY,
            "keyword": keyword,
            "date_from": start_date,
            "date_to": end_date,
            "page_size": 15  # 빠른 처리를 위해 15개로 제한
        }
        
        logger.info(f"🔍 해외 키워드 '{keyword}' 검색...")
        response = requests.get(base_url, params=params, timeout=5)  # 5초 타임아웃
        
        if response.status_code != 200:
            logger.error(f"❌ 해외 키워드 검색 API 호출 실패: {response.status_code}")
            return []
            
        response.raise_for_status()
        data = response.json()
        
        # 응답 구조 확인 및 기사 추출
        articles_data = []
        if 'data' in data:
            articles_data = data['data']
        elif 'articles' in data:
            articles_data = data['articles']
        elif isinstance(data, list):
            articles_data = data
        else:
            logger.warning(f"알 수 없는 해외 응답 구조: {list(data.keys())}")
            return []
        
        articles = []
        for item in articles_data:
            pub_date = item.get("published_at", "")
            if "T" in pub_date:
                article_date = pub_date.split("T")[0]
            else:
                article_date = pub_date
            if article_date:
                title = item.get("title", "")
                content = item.get("summary", "") or item.get("content", "")
                
                articles.append({
                    "id": generate_article_id(item),
                    "title": title,
                    "content": content,
                    "date": article_date,
                    "source_url": item.get("content_url", "") or item.get("url", ""),
                    "keyword": keyword,
                    "source": "해외"
                })
                
        # 중복 제거 (제목+내용 해시)
        unique_articles = []
        seen_hashes = set()
        for article in articles:
            hash_key = hash((article["title"].lower(), article["content"][:100].lower()))
            if hash_key not in seen_hashes:
                seen_hashes.add(hash_key)
                unique_articles.append(article)
        
        # 날짜순 정렬 (최신순)
        unique_articles.sort(key=lambda x: (
            x.get("date", "")
        ), reverse=True)
        
        logger.info(f"✅ 해외 '{keyword}' ({start_date}~{end_date}): {len(unique_articles)}개 관련 기사 검색 완료")
        return unique_articles[:12]
    except Exception as e:
        logger.error(f"❌ 해외 '{keyword}' 검색 오류: {e}")
        return []

@app.get("/api/articles")
async def get_articles(start_date: str = "2025-07-14", end_date: str = "2025-07-18", limit: int = 10):
    """기사 요약본 반환 API"""
    try:
        logger.info(f"📰 기사 요약본 요청 - 기간: {start_date} ~ {end_date}, 개수: {limit}")
        articles = await collect_it_news_from_deepsearch(start_date, end_date)
        if not articles:
            logger.warning("기사 없음: DeepSearch API 결과 없음")
            return JSONResponse(status_code=200, content={"articles": [], "message": "기사 없음", "total": 0})
        summarized_articles = []
        for article in articles[:limit]:
            content = article.get("content", "")
            summary = content[:200] + "..." if len(content) > 200 else content
            summarized_articles.append({
                "id": article.get("id", ""),
                "title": article.get("title", ""),
                "summary": summary,
                "date": article.get("date", ""),
                "source_url": article.get("source_url", ""),
                "keyword": article.get("keyword", "")
            })
        return {
            "articles": summarized_articles,
            "total": len(articles),
            "period": f"{start_date} ~ {end_date}",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"/api/articles 오류: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e), "articles": [], "total": 0})


# /api/keywords 엔드포인트(최신/정리본)
@app.get("/api/keywords")
async def get_weekly_keywords(start_date: str = "2025-07-14", end_date: str = "2025-07-18"):
    """DeepSearch → Azure AI Search → GPT-4o → Top 5 키워드 반환"""
    try:
        logger.info(f"🚀 News GPT v2 분석 시작 - 기간: {start_date} ~ {end_date}")
        if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, DEEPSEARCH_API_KEY]):
            logger.error("환경 변수 설정 오류: Azure OpenAI 또는 DeepSearch API 키가 설정되지 않음")
            return {
                "error": "환경 변수 설정 오류", 
                "keywords": [],
                "details": "Azure OpenAI 또는 DeepSearch API 키가 설정되지 않았습니다."
            }
        articles = await collect_it_news_from_deepsearch(start_date, end_date)
        if not articles:
            logger.warning("/api/keywords: 기사 없음")
            return {
                "error": "뉴스 수집 실패", 
                "keywords": [],
                "details": "DeepSearch API에서 기사를 가져올 수 없습니다."
            }
        logger.info(f"   ✅ {len(articles)}개 기사 수집 완료")
        # Azure AI Search 업로드 제거 (사용자 요청에 따라)
        logger.info("3️⃣ Azure OpenAI GPT-4o로 키워드 추출 중...")
        keywords = await extract_keywords_with_gpt4o(articles)
        if not keywords:
            logger.warning("/api/keywords: 키워드 추출 실패, 기본 키워드 사용")
            keywords = [
                {"keyword": "인공지능", "count": 25},
                {"keyword": "반도체", "count": 20},
                {"keyword": "클라우드", "count": 18},
                {"keyword": "메타버스", "count": 15},
                {"keyword": "블록체인", "count": 12}
            ]
        logger.info(f"   ✅ {len(keywords)}개 키워드 추출 완료")
        result = []
        for i, kw in enumerate(keywords[:5], 1):
            result.append({
                "rank": i,
                "keyword": kw['keyword'],
                "count": kw['count'],
                "source": "IT기술"
            })
        return {
            "keywords": result,
            "total_articles": len(articles),
            "date_range": f"{start_date} ~ {end_date}",
            "flow": "DeepSearch → Azure AI Search → GPT-4o",
            "status": "성공"
        }
    except Exception as e:
        logger.error(f"/api/keywords 전체 프로세스 오류: {e}", exc_info=True)
        return {
            "error": "시스템 오류",
            "keywords": [],
            "details": str(e),
            "fallback_keywords": [
                {"rank": 1, "keyword": "인공지능", "count": 25, "source": "IT기술"},
                {"rank": 2, "keyword": "반도체", "count": 20, "source": "IT기술"},
                {"rank": 3, "keyword": "클라우드", "count": 18, "source": "IT기술"},
                {"rank": 4, "keyword": "메타버스", "count": 15, "source": "IT기술"},
                {"rank": 5, "keyword": "블록체인", "count": 12, "source": "IT기술"}
            ]
        }




# API 호출에 재시도 적용
@retry_on_exception(max_retries=3, delay=0.5, backoff=2, allowed_exceptions=(requests.RequestException,))
def deepsearch_api_request(url, params):
    """DeepSearch API 요청 (재시도/로깅 일관성)"""
    logger.info(f"DeepSearch API 요청: {url} | params: {params}")
    response = requests.get(url, params=params, timeout=5)
    logger.info(f"DeepSearch 응답 코드: {response.status_code}")
    response.raise_for_status()
    return response.json()

async def collect_it_news_from_deepsearch(start_date: str, end_date: str):
    """DeepSearch API로 IT/기술 뉴스 수집 (새로운 구조에 맞춰 수정)"""
    if not DEEPSEARCH_API_KEY:
        logger.error("❌ DeepSearch API 키 없음")
        return []
    try:
        articles = []
        tech_keywords = ["IT", "기술", "인공지능", "AI", "반도체"]
        logger.info(f"🔍 DeepSearch API로 뉴스 수집 중... ({start_date} ~ {end_date})")
        
        for keyword in tech_keywords:
            try:
                # 사용자 제공 예시 URL 구조 사용
                base_url = DEEPSEARCH_KEYWORD_URL
                params = {
                    "api_key": DEEPSEARCH_API_KEY,
                    "keyword": keyword,  # 사용자 예시에 맞춰 keyword 파라미터 사용
                    "date_from": start_date,
                    "date_to": end_date
                }
                response = requests.get(base_url, params=params, timeout=5)
                
                if response.status_code != 200:
                    logger.warning(f"    ❌ '{keyword}' 검색 실패: {response.status_code}")
                    continue
                    
                data = response.json()
                
                # 응답 구조 확인
                if "data" in data:
                    articles_data = data["data"]
                elif "articles" in data:
                    articles_data = data["articles"]
                else:
                    logger.warning(f"    ⚠️ 알 수 없는 응답 구조: {list(data.keys())}")
                    continue
                    
                for item in articles_data:
                    pub_date = item.get("published_at", "")
                    if "T" in pub_date:
                        article_date = pub_date.split("T")[0]
                    else:
                        article_date = pub_date
                    title = item.get("title", "").strip()
                    content = (item.get("summary", "") or item.get("content", "")).strip()
                    if title and content:
                        articles.append({
                            "id": f"news_{keyword}_{hash(title)%100000}",
                            "title": title,
                            "content": content,
                            "date": article_date,
                            "source_url": item.get("content_url", "") or item.get("url", ""),
                            "keyword": keyword
                        })
                logger.info(f"    ✅ '{keyword}': {len(articles_data)}개 기사 수집")
                # time.sleep(0.2)  # 속도 향상을 위해 제거
            except Exception as e:
                logger.warning(f"    ❌ '{keyword}' 처리 오류: {e}")
                continue
                
        # 중복 제거 (제목+내용 해시)
        unique_articles = []
        seen_hashes = set()
        for article in articles:
            hash_key = hash((article["title"].lower(), article["content"][:100].lower()))
            if hash_key not in seen_hashes:
                seen_hashes.add(hash_key)
                unique_articles.append(article)
        logger.info(f"✅ 총 {len(unique_articles)}개 고유 기사 수집 완료")
        return unique_articles[:30]
    except Exception as e:
        logger.error(f"❌ DeepSearch API 전체 오류: {e}", exc_info=True)
        # 샘플 데이터 반환 (API 실패 시)
        return [
            {
                "id": "sample_1",
                "title": "AI 기술 발전으로 IT 업계 변화 가속화",
                "content": "인공지능 기술의 급속한 발전으로 IT 업계 전반에 변화가 일어나고 있다. 머신러닝과 딥러닝 기술을 활용한 새로운 서비스들이 등장하고 있으며, 기업들은 디지털 트랜스포메이션을 가속화하고 있다.",
                "date": start_date,
                "source_url": "https://example.com/ai-news",
                "keyword": "AI"
            },
            {
                "id": "sample_2",
                "title": "반도체 산업 회복 조짐, 글로벌 공급망 안정화",
                "content": "반도체 산업이 회복 조짐을 보이며 글로벌 공급망이 안정화되고 있다. 주요 반도체 기업들의 실적이 개선되고 있으며, 새로운 기술 개발에 대한 투자도 증가하고 있다.",
                "date": start_date,
                "source_url": "https://example.com/semiconductor-news",
                "keyword": "반도체"
            }
        ]


# Azure AI Search 함수 제거됨 (사용자 요청에 따라 DeepSearch만 사용)

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
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "뉴스 키워드 분석 전문가입니다. 기사에서 중요한 키워드를 추출합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.2
        )
        
        keywords_text = response.choices[0].message.content or ""
        print(f"GPT-4o 응답: {keywords_text}")
        
        # 키워드 파싱
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
        
        # 키워드가 추출되지 않은 경우 기본 키워드 제공
        if not keywords:
            print("⚠️ GPT-4o에서 키워드 추출 실패, 기본 키워드 사용")
            keywords = [
                {"keyword": "IT", "count": 20},
                {"keyword": "기술", "count": 18},
                {"keyword": "디지털", "count": 15},
                {"keyword": "정보", "count": 12},
                {"keyword": "시스템", "count": 10}
            ]
        
        # 빈도 기준 정렬
        keywords.sort(key=lambda x: x['count'], reverse=True)
        
        print(f"✅ {len(keywords)}개 키워드 추출 완료")
        return keywords
        
    except Exception as e:
        print(f"❌ GPT-4o 오류: {e}")
        return []

# 새로운 엔드포인트 추가 - 시각별 분석과 챗봇 기능


from fastapi import Request
from fastapi.responses import JSONResponse

@app.post("/chat")
async def chat(request: Request):
    """산업별 키워드 분석 기반 동적 챗봇"""
    try:
        data = await request.json()
        question = data.get("question") or data.get("message") or ""
        if not question:
            return JSONResponse(content={"answer": "질문을 입력해주세요."})
        # 1. 질문에서 키워드 추출 및 산업 분류
        keyword_info = extract_keyword_and_industry(question)
        # 2. 현재 주간 키워드 가져오기
        current_keywords = get_current_weekly_keywords()
        # 3. 질문 유형에 따른 동적 응답
        if keyword_info["type"] == "industry_analysis":
            answer = generate_industry_based_answer(
                question,
                keyword_info["keyword"],
                keyword_info["industry"],
                current_keywords
            )
        elif keyword_info["type"] == "keyword_trend":
            answer = generate_keyword_trend_answer(question, keyword_info["keyword"])
        elif keyword_info["type"] == "comparison":
            answer = generate_comparison_answer(question, keyword_info["keywords"])
        else:
            answer = generate_contextual_answer(question, current_keywords)
        return JSONResponse(content={"answer": answer})
    except Exception as e:
        logger.error(f"/chat 오류: {e}", exc_info=True)
        return JSONResponse(content={"answer": f"답변 생성 중 오류가 발생했습니다: {str(e)}"}, status_code=500)

def extract_keyword_and_industry(question):
    """질문에서 키워드와 산업 분류 추출"""
    
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
        # 직접적인 키워드 분석 대신 현재 주차의 대표 키워드 반환
        return ["인공지능", "반도체", "기술혁신"]
    except Exception as e:
        print(f"키워드 추출 오류: {e}")
        return ["인공지능", "반도체", "기업"]

def generate_industry_based_answer(question, keyword, industry, current_keywords):
    """산업별 키워드 분석 기반 답변 생성"""
    try:
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

{industry} 관점에서 '{keyword}'에 대해 답변해주세요.

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
        prompt = f"""
질문: {question}
키워드: {keyword}

'{keyword}'의 최근 트렌드를 분석해주세요.

분석 내용:
1. 최근 '{keyword}' 관련 주요 뉴스 동향
2. 시간적 변화와 발전 방향
3. 향후 전망과 관심 포인트

시간순으로 정리하여 트렌드를 명확하게 설명해주세요.
"""
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"당신은 '{keyword}' 분야의 트렌드 분석 전문가입니다. 최신 동향과 변화를 분석합니다."},
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
        prompt = f"""
질문: {question}
비교 대상: {', '.join(keywords)}

키워드들을 비교 분석해주세요.

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
                {"role": "system", "content": f"당신은 다양한 키워드를 비교 분석하는 전문가입니다. 객관적으로 비교 분석합니다."},
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
        # 현재 주간 키워드 컨텍스트 추가
        keywords_context = f"현재 주간 핵심 키워드: {', '.join(current_keywords)}"
        
        prompt = f"""
질문: {question}
{keywords_context}

현재 주간 핵심 키워드들과 연관지어 답변하되, 질문의 맥락을 정확히 파악하여 답변해주세요.

답변 시 고려사항:
1. 현재 주간 핵심 키워드와의 연관성 언급
2. 구체적인 사례와 데이터 활용  
3. 균형잡힌 시각으로 설명
4. 실용적인 정보 제공

명확하고 도움이 되는 답변을 제공해주세요.
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

@app.get("/weekly-keywords-by-date")
async def get_weekly_keywords_by_date(start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"), 
                               end_date: str = Query(..., description="종료일 (YYYY-MM-DD)"),
                               region: str = Query("domestic", description="지역 (domestic/global)")):
    """날짜별 주간 키워드 반환 (프론트에서 요청하는 엔드포인트) - 실제 API 호출"""
    try:
        logger.info(f"📅 날짜별 키워드 요청: {start_date} ~ {end_date} ({region})")
        
        # 지역별로 다른 처리
        if region == "global":
            # 해외 키워드는 샘플 데이터 사용 (DeepSearch에 world 카테고리가 있다면 활용 가능)
            keywords = get_sample_global_keywords_by_date(start_date, end_date)
            tech_articles_count = 0
        else:
            # 국내는 기존 Tech 워크플로우 사용
            tech_articles = await fetch_tech_articles(start_date, end_date)
            if not tech_articles:
                logger.warning(f"❌ Tech 기사 없음: {start_date} ~ {end_date}")
                keywords = get_sample_keywords_by_date(start_date, end_date)
                tech_articles_count = 0
            else:
                # GPT로 키워드 추출
                extracted_keywords = await extract_keywords_with_gpt(tech_articles)
                if extracted_keywords:
                    keywords = [kw["keyword"] for kw in extracted_keywords[:3]]  # 상위 3개만
                else:
                    keywords = get_sample_keywords_by_date(start_date, end_date)
                tech_articles_count = len(tech_articles)
        
        # 응답 형식을 프론트 요구사항에 맞게 조정 (키워드 배열로 반환)
        response_data = {
            "keywords": keywords,  # 단순 문자열 배열로 반환
            "date_range": f"{start_date} ~ {end_date}",
            "total_count": len(keywords),
            "tech_articles_count": tech_articles_count,
            "region": region,
            "status": "success"
        }
        return JSONResponse(content=response_data, media_type="application/json; charset=utf-8")
    except Exception as e:
        logger.error(f"날짜별 키워드 요청 오류: {e}")
        return JSONResponse(status_code=500, content={
            "error": str(e),
            "keywords": [],
            "date_range": f"{start_date} ~ {end_date}",
            "region": region,
            "status": "error"
        })

@app.get("/global-weekly-keywords-by-date")
async def get_global_weekly_keywords_by_date(start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"), 
                               end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")):
    """해외 날짜별 주간 키워드 반환 (프론트에서 요청하는 엔드포인트) - 실제 API 호출"""
    try:
        logger.info(f"🌍 해외 날짜별 키워드 요청: {start_date} ~ {end_date}")
        
        # 해외 Tech 기사 → GPT 키워드 추출 워크플로우 사용
        global_tech_articles = await fetch_global_tech_articles(start_date, end_date)
        if not global_tech_articles:
            logger.warning(f"❌ 해외 Tech 기사 없음: {start_date} ~ {end_date}")
            # 해외 샘플 키워드 반환
            keywords = get_global_sample_keywords_by_date(start_date, end_date)
        else:
            # GPT로 키워드 추출 (해외 기사용)
            extracted_keywords = await extract_keywords_with_gpt(global_tech_articles)
            if extracted_keywords:
                keywords = [kw["keyword"] for kw in extracted_keywords[:3]]  # 상위 3개만
            else:
                keywords = get_global_sample_keywords_by_date(start_date, end_date)
        
        # 응답 형식을 프론트 요구사항에 맞게 조정 (키워드 배열로 반환)
        response_data = {
            "keywords": keywords,  # 단순 문자열 배열로 반환
            "date_range": f"{start_date} ~ {end_date}",
            "total_count": len(keywords),
            "global_tech_articles_count": len(global_tech_articles) if global_tech_articles else 0,
            "region": "global",
            "status": "success"
        }
        return JSONResponse(content=response_data, media_type="application/json; charset=utf-8")
    except Exception as e:
        logger.error(f"해외 날짜별 키워드 요청 오류: {e}")
        return JSONResponse(status_code=500, content={
            "error": str(e),
            "keywords": [],
            "date_range": f"{start_date} ~ {end_date}",
            "region": "global",
            "status": "error"
        })

def get_global_sample_keywords_by_date(start_date: str, end_date: str):
    """해외 주간별 샘플 키워드 반환"""
    global_keywords_map = {
        "2025-07-01": ["AI Revolution", "Quantum Computing", "Green Tech"],
        "2025-07-06": ["ChatGPT-5", "Tesla Robotics", "Web3"],
        "2025-07-14": ["Neural Chips", "Space Tech", "Bio Computing"]
    }
    
    # 날짜에 해당하는 키워드 찾기
    for date_key, keywords in global_keywords_map.items():
        if start_date >= date_key:
            return keywords
    
    # 기본 해외 키워드
    return ["AI Technology", "Innovation", "Future Tech"]

@app.get("/weekly-keywords")
def get_weekly_keywords():
    """주간 Top 3 키워드 반환"""
    try:
        # 샘플 키워드 (실제로는 DeepSearch API나 데이터에서 가져오기)
        response_data = {
            "keywords": ["인공지능", "반도체", "기술혁신"],
            "week_info": "7월 3주차 (2025.07.14~07.18) - AI 뉴스 분석"
        }
        return JSONResponse(content=response_data, media_type="application/json; charset=utf-8")
    except Exception as e:
        response_data = {
            "keywords": ["인공지능", "반도체", "기업"],
            "week_info": "7월 3주차 (2025.07.14~07.18) - AI 뉴스 분석"
        }
        return JSONResponse(content=response_data, media_type="application/json; charset=utf-8")

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

def get_sample_global_keywords_by_date(start_date: str, end_date: str):
    """날짜에 따른 해외 샘플 키워드 반환"""
    if "07-01" in start_date:  # 7월 1주차
        return ["Tesla", "Apple", "Microsoft"]
    elif "07-06" in start_date:  # 7월 2주차  
        return ["ChatGPT", "OpenAI", "Meta"]
    elif "07-14" in start_date:  # 7월 3주차
        return ["Google", "NVIDIA", "Amazon"]
    else:
        return ["Tech", "Innovation", "AI"]

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
        # 기존 분석
        main_completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"{industry} 분야 전문가로서 키워드에 대한 긍정적 분석을 제공합니다."},
                {"role": "user", "content": main_prompt}
            ]
        )
        
        # 정반대 관점 분석
        counter_completion = openai_client.chat.completions.create(
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

@app.post("/chat")
async def chat(request: Request):
    """개선된 챗봇 - 주간요약 키워드 클릭 오류 해결"""
    try:
        data = await request.json()
        question = data.get("question") or data.get("message") or ""
        
        if not question:
            return JSONResponse(content={"answer": "질문을 입력해주세요."})
        
        # 안전한 답변 생성 (오류 방지)
        try:
            completion = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 IT/기술 뉴스 분석 전문가입니다. 사용자의 질문에 간결하고 정확하게 답변해주세요."},
                    {"role": "user", "content": question}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            answer = completion.choices[0].message.content or "답변을 생성할 수 없습니다."
            
        except Exception as api_error:
            logger.error(f"OpenAI API 오류: {api_error}")
            answer = "현재 AI 서비스에 일시적인 문제가 있습니다. 잠시 후 다시 시도해주세요."
        
        return JSONResponse(content={"answer": answer})
        
    except Exception as e:
        logger.error(f"/chat 오류: {e}", exc_info=True)
        return JSONResponse(content={
            "answer": "챗봇 서비스에 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        }, status_code=200)  # 200으로 반환하여 프론트엔드 오류 방지

@app.post("/keyword-analysis")
def analyze_keyword_dynamically(request: dict):
    """동적 키워드 분석 - 클릭된 키워드에 대한 다각도 분석"""
    keyword = request.get("keyword", "")
    
    if not keyword:
        raise HTTPException(status_code=400, detail="키워드를 제공해야 합니다.")
    
    try:
        # 키워드에 대한 다각도 분석
        prompt = f"""
키워드: '{keyword}'

다음 5가지 관점에서 이 키워드를 분석해주세요:
1. 사회적 영향
2. 경제적 측면  
3. 기술적 관점
4. 문화적 의미
5. 미래 전망

각 관점별로 2-3문장씩 간결하게 설명해주세요.
"""
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 다양한 관점에서 키워드를 분석하는 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
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

# =============================================================================
# 서버 실행 설정
# =============================================================================

if __name__ == "__main__":
    logger.info("🚀 News GPT v2 서버 시작 (새로운 워크플로우)")
    logger.info("📋 워크플로우:")
    logger.info("   1️⃣ Tech기사수집 (DeepSearch Tech)")
    logger.info("   2️⃣ GPT키워드추출")
    logger.info("   3️⃣ 키워드기사검색 (DeepSearch Keyword)")
    logger.info("   4️⃣ 기사클릭 → URL리다이렉트")
    logger.info("🌐 서버 주소: http://localhost:8000")
    
    # FastAPI 서버 직접 실행
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)