# News GPT v2 - 새로운 구조 (DeepSearch 기반 워크플로우)
import os
import re
import time
import asyncio  # 추가
import logging
import requests
import hashlib
import uvicorn
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AzureOpenAI
from functools import wraps
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from apscheduler.schedulers.background import BackgroundScheduler


# keyword explainer
import urllib.parse
import feedparser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from googletrans import Translator
from dateutil import parser as date_parser
from concurrent.futures import ThreadPoolExecutor  # ✅ 추가


# 로깅 설정 (최적화)
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("news_gpt_v2")

# 환경변수 로드
load_dotenv()

CACHE_GOOGLE_TRENDING_KEYWORDS = None
def cache_google_tranding(country_codes):
    global CACHE_GOOGLE_TRENDING_KEYWORDS

    def fetch_keywords(geo):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        keywords = []
        try:
            url = f"https://trends.google.com/trending?geo={geo}&hl=en&category=3&hours=24&sort=search-volume"
            driver.get(url)
            time.sleep(4)
            elems = driver.find_elements(By.CLASS_NAME, 'mZ3RIc') or driver.find_elements(By.CSS_SELECTOR, '[data-ved]')
            keywords = [e.text.strip() for e in elems if e.text.strip()][:10]
        except Exception as e:
            print(f"Error fetching trends for {geo}: {e}")
            keywords = [f"Sample keyword {i} for {geo}" for i in range(1, 6)]
        finally:
            driver.quit()
        return [{"country": geo, "keyword": kw} for kw in keywords]

    # ✅ 병렬 실행
    with ThreadPoolExecutor(max_workers=min(len(country_codes), 5)) as executor:
        results = list(executor.map(fetch_keywords, country_codes))

    raw_keywords = [item for sublist in results for item in sublist]
            
    shared_indices = find_shared_keywords_with_llm(raw_keywords)

    for i, item in enumerate(raw_keywords):
        item["shared"] = i in shared_indices

    CACHE_GOOGLE_TRENDING_KEYWORDS = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "data": raw_keywords,
        "status": "success"
    }

# FastAPI 시작 시 캐시 백엔드 초기화
def start():
    country_codes = ['KR', 'US', 'MX', 'GB', 'IN', 'ZA', 'AU']
    cache_google_tranding(country_codes)

    scheduler = BackgroundScheduler()
    scheduler.add_job(cache_google_tranding, trigger="cron", minute=0, args=[country_codes])
    scheduler.start()
    
@asynccontextmanager
async def lifespan(_: FastAPI):
    # When service starts.
    start()
    yield
    
    
# FastAPI 앱 인스턴스 생성
app = FastAPI(title="News GPT v2", description="AI 뉴스 키워드 분석 플랫폼", lifespan=lifespan)

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
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

AZURE_OPENAI_KEYWORD_EXPLAINER_API_KEY = os.getenv("AZURE_OPENAI_KEYWORD_EXPLAINER_API_KEY")
AZURE_OPENAI_KEYWORD_EXPLAINER_ENDPOINT = os.getenv("AZURE_OPENAI_KEYWORD_EXPLAINER_ENDPOINT")
AZURE_OPENAI_KEYWORD_EXPLAINER_DEPLOYMENT = os.getenv("AZURE_OPENAI_KEYWORD_EXPLAINER_DEPLOYMENT")
AZURE_OPENAI_KEYWORD_EXPLAINER_VERSION = os.getenv("AZURE_OPENAI_KEYWORD_EXPLAINER_VERSION")

DEEPSEARCH_API_KEY = os.getenv("DEEPSEARCH_API_KEY")

# 이메일 설정 (Gmail SMTP 사용)
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = os.getenv("EMAIL_USER")  # Gmail 주소
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Gmail 앱 비밀번호

# Pydantic 모델
class SubscriptionRequest(BaseModel):
    email: str

class EmailInsightRequest(BaseModel):
    email: str

# RAG 분석 요청 모델
class JobAnalysisRequest(BaseModel):
    query: str
    selected_keyword: Optional[str] = None
    selected_keyword_reason: Optional[str] = None # ✅ 이 줄을 추가합니다.

# 👇 여기에 새로운 Pydantic 모델을 추가합니다.
class IndustryKeywordAnalysisRequest(BaseModel):
    industry_perspective: str # 분석 관점 (예: "데이터 과학자")
    target_keyword: str       # 분석 대상 키워드 (예: "인공지능")
    # 기존 IndustryAnalysisRequest에서 industry와 keyword를 대체

class TrendRequest(BaseModel):
    keyword: str
    country: str
    headlines: List[str]

# Azure OpenAI 클라이언트 초기화
openai_client = AzureOpenAI(
    api_key=str(AZURE_OPENAI_API_KEY),
    api_version=str(AZURE_OPENAI_API_VERSION),
    azure_endpoint=str(AZURE_OPENAI_ENDPOINT)
)

openai_keyword_explainer_client = AzureOpenAI(
    api_key=str(AZURE_OPENAI_KEYWORD_EXPLAINER_API_KEY),
    api_version=str(AZURE_OPENAI_KEYWORD_EXPLAINER_VERSION),
    azure_endpoint=str(AZURE_OPENAI_KEYWORD_EXPLAINER_ENDPOINT)
)

translator = Translator()
sentence_transformer_model = SentenceTransformer('all-MiniLM-L6-v2')

# 환경 변수 로드 (이 변수들은 .env 파일에 설정되어 있어야 합니다)
AZURE_SEARCH_ENDPOINT_NCS = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY_NCS = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX_NCS = os.getenv("AZURE_SEARCH_INDEX")
AZURE_OPENAI_DEPLOYMENT_NCS = os.getenv("AZURE_OPENAI_DEPLOYMENT") # .env에 설정한 배포 이름 (e.g., donghwi_JD_gpt-4o)

# Azure AI Search 클라이언트 초기화
ncs_search_client: Optional[SearchClient] = None
ncs_search_client: Optional[SearchClient] = None
if AZURE_SEARCH_ENDPOINT_NCS and AZURE_SEARCH_KEY_NCS and AZURE_SEARCH_INDEX_NCS:
    try:
        ncs_search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT_NCS,
            index_name=AZURE_SEARCH_INDEX_NCS,
            credential=AzureKeyCredential(AZURE_SEARCH_KEY_NCS)
        )
        logger.info(f"✅ Azure AI Search (NCS) 클라이언트 초기화 성공: {AZURE_SEARCH_INDEX_NCS}")
    except Exception as e:
        logger.error(f"❌ Azure AI Search (NCS) 클라이언트 초기화 실패: {e}", exc_info=True)
        ncs_search_client = None
else:
    logger.warning("⚠️ Azure AI Search (NCS) 환경 변수 (AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX) 중 일부 또는 전부가 설정되지 않아 NCS 검색 기능을 사용할 수 없습니다. .env 파일을 확인하세요.")

# NCS 문서 검색 함수
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
        search_results = await asyncio.to_thread( # requests는 동기 함수이므로 asyncio.to_thread 사용
            ncs_search_client.search,
            search_text=query,
            query_type="semantic",
            semantic_configuration_name="default", # .env의 AZURE_OPENAI_DEPLOYMENT_NCS와 연동
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

# 직무/산업 요약 함수 (RAG 핵심)
async def get_job_industry_summary(query: str) -> str:
    """사용자 질문에 기반하여 NCS 직무/산업 정보 요약 (AI 활용)"""
    logger.info(f"🧠 get_job_industry_summary 호출 - 쿼리: {query}")
    context_text = await search_ncs_documents(query) # NCS 문서 검색

    if not context_text:
        logger.warning("❗ 관련된 직무/산업 정보를 찾을 수 없어 일반 GPT 답변을 시도합니다.")
        system_msg = "너는 직무/산업 관련 전문가 AI야."
        user_prompt = f"'{query}'에 대해 간략하게 요약해줘."
        try:
            response = openai_client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NCS, # .env의 AZURE_OPENAI_DEPLOYMENT 사용
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
            model=AZURE_OPENAI_DEPLOYMENT_NCS, # .env의 AZURE_OPENAI_DEPLOYMENT 사용
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


# DeepSearch API URLs (국내 + 해외)
DEEPSEARCH_TECH_URL = "https://api-v2.deepsearch.com/v1/articles/tech"
DEEPSEARCH_KEYWORD_URL = "https://api-v2.deepsearch.com/v1/articles"
DEEPSEARCH_GLOBAL_TECH_URL = "https://api-v2.deepsearch.com/v1/global-articles"
DEEPSEARCH_GLOBAL_KEYWORD_URL = "https://api-v2.deepsearch.com/v1/global-articles"


# API 호출 재시도 데코레이터 (최적화)
def retry_on_exception(max_retries=1, delay=0.1, backoff=1.2, allowed_exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except allowed_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"⚡ {func.__name__} 재시도 {attempt + 1}/{max_retries}, {wait_time:.1f}초 후")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"❌ {func.__name__} 최종 실패: {str(e)}")
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except allowed_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"⚡ {func.__name__} 재시도 {attempt + 1}/{max_retries}, {wait_time:.1f}초 후")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ {func.__name__} 최종 실패: {str(e)}")
            raise last_exception
        
        # 함수가 코루틴인지 확인
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator

# =============================================================================
# 새로운 워크플로우 API 엔드포인트들
# =============================================================================

@app.get("/")
async def serve_home():
    """메인 페이지 제공"""
    return FileResponse("index.html")

@app.get("/analysis.html")
async def serve_analysis():
    """상세 분석 페이지 제공"""
    return FileResponse("analysis.html")

@app.get("/news-detail.html")
async def serve_news_detail():
    """뉴스 상세 페이지 제공 (유튜브 스타일)"""
    return FileResponse("news-detail.html")

@app.get("/trending.html")
async def serve_trending():
    """트렌딩 페이지 제공"""
    return FileResponse("trending.html")

@app.get("/admin.html")
async def serve_admin():
    """관리자 페이지 제공"""
    return FileResponse("admin.html")


# 4단계: 키워드 클릭시 관련 기사 노출
@app.get("/api/keyword-articles/{keyword}")
async def get_keyword_articles(keyword: str, 
                              start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
                              end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")):
    """키워드 클릭시 관련 기사들을 반환"""
    try:
        # undefined 키워드 처리
        if keyword == "undefined" or not keyword or keyword.strip() == "":
            logger.warning(f"⚠️ 잘못된 키워드 '{keyword}' 요청 - 기본 키워드로 대체")
            keyword = "AI"  # 기본 키워드로 대체
        
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
# 직무/산업 분석 API 엔드포인트
# =============================================================================

@app.post("/api/job-analysis")
async def analyze_job_industry(request: JobAnalysisRequest):
    user_job_role = request.query             # 사용자 입력 직무/산업 (분석 관점)
    analysis_keyword = request.selected_keyword # 분석 대상 키워드
    analysis_keyword_reason = request.selected_keyword_reason # ✅ 키워드 선정 이유

    # analysis_keyword가 제공되지 않았을 때 reason도 기본값으로 설정 (선택 사항)
    if not analysis_keyword:
        analysis_keyword = "인공지능"
        analysis_keyword_reason = "사용자가 선택하지 않아 기본값으로 설정됨" # 필요에 따라 기본 이유 설정
        logger.warning(f"⚠️ analysis_keyword가 제공되지 않아 '{analysis_keyword}'를 기본값으로 사용합니다.")


    if not user_job_role:
        raise HTTPException(status_code=400, detail="분석할 직무/산업을 입력해야 합니다.")

    logger.info(f"📊 직무/산업 분석 요청: 관점='{user_job_role}', 대상 키워드='{analysis_keyword}'")

    try:
        # 1단계: 직무 요약 (NCS RAG) - 기존 로직
        summary = await get_job_industry_summary(user_job_role) # user_job_role을 쿼리로 전달

        # 2단계: 긍정적/비판적 분석 생성 (user_job_role 관점에서 analysis_keyword 분석)
        insight_analysis_result = await generate_industry_based_answer(
            question=f"'{analysis_keyword}'에 대한 '{user_job_role}' 직무 관점에서의 긍정적 분석",
            keyword=analysis_keyword,
            industry=user_job_role,
            current_keywords=[analysis_keyword],
            reason=analysis_keyword_reason # ✅ 이유 전달
        )

        # generate_comparison_answer 함수를 '직무 관점'에서 특정 키워드를 분석하도록 활용
        counter_analysis_result = await generate_comparison_answer(
            question=f"'{analysis_keyword}'에 대한 '{user_job_role}' 직무 관점에서의 비판적 분석",
            keywords=[analysis_keyword],
            perspective_role=user_job_role,
            reason=analysis_keyword_reason # ✅ 이유 전달
        )

        if not summary:
            logger.warning(f"⚠️ 직무/산업 요약 결과 없음 또는 오류 발생 for query: {user_job_role}")
            return JSONResponse(status_code=500, content={"error": "직무/산업 정보를 분석할 수 없습니다. 더 구체적인 질문을 해주세요."})

        logger.info(f"✅ 직무/산업 분석 완료. 요약 길이: {len(summary)}")
        return {
            "query": user_job_role,
            "summary": summary,
            "insight_analysis": insight_analysis_result,
            "counter_insight_analysis": counter_analysis_result,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"❌ 직무/산업 분석 엔드포인트 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"직무/산업 분석 중 서버 오류 발생: {str(e)}")
    
    
# =============================================================================
# 새로운 워크플로우 핵심 함수들
# =============================================================================

# 메모리 저장소 (최적화된 캐싱 시스템)
articles_cache = {}  # {article_id: {url, title, content, ...}}
keywords_cache = {}  # {keyword: [article_ids]}
api_cache = {}  # API 응답 캐시 {endpoint_params: response_data}
cache_timestamps = {}  # 캐시 생성 시간 저장

# 캐시 설정
CACHE_EXPIRY_MINUTES = 30  # 30분 캐시 유지
MAX_CACHE_SIZE = 1000  # 최대 캐시 항목 수

# 캐시 관리 함수들
def get_cache_key(*args, **kwargs):
    """캐시 키 생성"""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()

def is_cache_valid(cache_key):
    """캐시 유효성 검사"""
    if cache_key not in cache_timestamps:
        return False
    
    created_time = cache_timestamps[cache_key]
    current_time = time.time()
    age_minutes = (current_time - created_time) / 60
    
    return age_minutes < CACHE_EXPIRY_MINUTES

def set_cache(cache_key, data):
    """캐시 저장"""
    # 캐시 크기 제한
    if len(api_cache) >= MAX_CACHE_SIZE:
        # 가장 오래된 캐시 제거
        oldest_key = min(cache_timestamps.keys(), key=lambda k: cache_timestamps[k])
        del api_cache[oldest_key]
        del cache_timestamps[oldest_key]
    
    api_cache[cache_key] = data
    cache_timestamps[cache_key] = time.time()
    logger.info(f"💾 캐시 저장: {cache_key[:8]}... (총 {len(api_cache)}개)")

def get_cache(cache_key):
    """캐시 조회"""
    if cache_key in api_cache and is_cache_valid(cache_key):
        logger.info(f"⚡ 캐시 히트: {cache_key[:8]}...")
        return api_cache[cache_key]
    return None

# 1단계: DeepSearch Tech에서 기사 수집
@retry_on_exception(max_retries=1, delay=0.1, backoff=1.5, allowed_exceptions=(requests.RequestException,))
async def fetch_tech_articles(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """DeepSearch Tech 카테고리에서 기사들을 수집합니다 (빠른 처리)"""
    if not DEEPSEARCH_API_KEY:
        logger.error("❌ DeepSearch API 키가 설정되지 않음")
        return []
    
    try:
        # 충분한 기사 수집으로 더 정확한 키워드 분석
        base_url = DEEPSEARCH_TECH_URL
        params = {
            "api_key": DEEPSEARCH_API_KEY,
            "date_from": start_date,
            "date_to": end_date,
            "page_size": 50  # 20개에서 50개로 증가하여 더 많은 데이터 수집
        }
        
        logger.info(f"� Tech 기사 수집 중...")
        response = requests.get(base_url, params=params, timeout=15)  # 15초로 수정
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
            "page_size": 50  # 20개에서 50개로 증가하여 더 많은 데이터 수집
        }
        
        logger.info(f"🌍 해외 Tech 기사 수집 중...")
        response = requests.get(base_url, params=params, timeout=15)  # 5초->15 타임아웃
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
# GPT가 키워드를 추출한 이유도 함께 반환하도록 수정
async def extract_keywords_with_gpt(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """GPT를 사용해 기사들에서 키워드를 추출하고, 각 키워드 선정 이유를 함께 반환합니다."""
    if not articles:
        logger.warning("❌ 분석할 기사가 없습니다")
        return []

    try:
        top_articles = articles[:10]
        titles_text = "\n".join([f"- {article['title']}" for article in top_articles])

        prompt = f"""다음 IT기술 뉴스 제목에서 핵심 키워드 5개를 추출하고, 각 키워드를 선정한 간략한 이유를 함께 제공하세요.

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
        
        # --- 핵심 수정 부분 시작 ---
        # 1단계: GPT 응답의 다중 줄 패턴을 단일 줄로 통합
        # "키워드N: [키워드]\n선정 이유N: [이유]" 패턴을 "키워드N: [키워드] 선정 이유N: [이유]"로 변경
        # 이렇게 하면 각 키워드-이유 쌍이 하나의 'line'으로 인식될 가능성이 높아집니다.
        # \s*:\s* 는 ': ' 앞뒤의 공백을 처리, (.+?)\n\s*선정 이유(\d+):\s* 는 다중 줄 패턴을 찾음
        processed_text = re.sub(
            r'(키워드(\d+):\s*(.+?))\n\s*(선정 이유\2:\s*(.+?))',
            r'\1 \4', # 키워드: [키워드] 선정 이유N: [이유] 형태로 통합
            keywords_with_reasons_text,
            flags=re.IGNORECASE | re.DOTALL # re.DOTALL은 .이 \n도 포함하도록 함
        )

        # 처리된 텍스트를 다시 줄 단위로 분리
        lines = processed_text.strip().split('\n')
        # --- 핵심 수정 부분 끝 ---

        # 🚨 빈 라인을 제거하는 필터링을 먼저 적용합니다.
        filtered_lines = [line.strip() for line in lines if line.strip()]

        for i, line in enumerate(filtered_lines):
            keyword_raw = ""
            reason = "이유 없음"

            # 1. 콜론으로 키워드와 이유 분리 시도
            # 이제 line은 "키워드N: [키워드] 선정 이유N: [이유]" 또는 "키워드: [이유]" 형태일 가능성이 높음
            if ':' in line:
                # 첫 번째 콜론을 기준으로 분리 (키워드 부분과 나머지)
                first_colon_idx = line.find(':')
                keyword_part = line[:first_colon_idx].strip()
                rest_of_line = line[first_colon_idx+1:].strip()

                # '선정 이유N:' 패턴을 포함하는지 확인하고 이유를 추출
                reason_match = re.search(r'선정 이유\d+:\s*(.+)', rest_of_line, re.IGNORECASE)
                if reason_match:
                    reason = reason_match.group(1).strip()
                    # 키워드 부분에서 '선정 이유N:' 부분을 제거
                    keyword_raw = re.sub(r'선정 이유\d+:\s*.+', '', rest_of_line, re.IGNORECASE).strip()
                else:
                    # '선정 이유N:' 패턴이 없으면, rest_of_line 전체를 이유로 간주
                    reason = rest_of_line
                    keyword_raw = keyword_part
            else:
                keyword_raw = line.strip()
                reason = "GPT가 선정 이유를 제공하지 않았습니다." # 이유가 없는 경우 기본 메시지

            # 2. '키워드N: ', 'KeywordN: ', 'N. ' 등의 패턴을 더 강력하게 제거
            keyword_final = re.sub(r'^(키워드\d+|Keyword\d+|\d+\.)\s*', '', keyword_raw, flags=re.IGNORECASE).strip()

            # 3. 문장 시작의 특수문자 제거 (예: `- 유튜브:`)
            keyword_final = re.sub(r'^[^\w\s]*', '', keyword_final).strip()

            # 4. 허용된 문자(한글, 영어, 숫자, 공백, 하이픈, 슬래시) 외 모두 제거
            keyword_final = re.sub(r'[^\w\s\-/가-힣]', '', keyword_final).strip()

            # 5. 마지막에 남을 수 있는 콜론/점 제거
            keyword_final = re.sub(r'[:.]$', '', keyword_final).strip()

            # 최종적으로 빈 문자열이 되거나 유효하지 않은 키워드는 추가하지 않습니다.
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

        # 유효한 키워드가 부족할 때만 샘플 키워드를 사용합니다.
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
    

# 2단계-해외: 해외 기사에서 영어 키워드 추출 
async def extract_global_keywords_with_gpt(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """GPT를 사용해 해외 기사들에서 영어 키워드를 추출하고, 각 키워드 선정 이유를 함께 반환합니다."""
    if not articles:
        logger.warning("❌ 분석할 해외 기사가 없습니다")
        return []
    
    try:
        top_articles = articles[:10]
        titles_text = "\n".join([f"- {article['title']}" for article in top_articles])

        # GPT 프롬프트는 그대로 유지
        prompt = f"""Extract 5 key English tech keywords from these global news titles:

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
        
        # 🚨 빈 라인을 제거하는 필터링을 먼저 적용합니다.
        filtered_lines = [line.strip() for line in lines if line.strip()]

        for i, line in enumerate(filtered_lines):
            keyword_raw = ""
            reason = "Reason not provided by AI."
            
            # 1. 콜론으로 키워드와 이유 분리 시도
            if ':' in line:
                parts = line.split(':', 1)
                keyword_raw = parts[0].strip()
                reason = parts[1].strip()
            else:
                keyword_raw = line.strip()
                reason = "Reason not provided by AI." # 이유가 없는 경우 기본 메시지

            # 2. 'KeywordN: ', 'N. ' 등의 패턴을 더 강력하게 제거
            keyword_final = re.sub(r'^(Keyword\d+|\d+\.)\s*:\s*', '', keyword_raw, flags=re.IGNORECASE).strip()

            # 3. 문장 시작의 특수문자 제거
            keyword_final = re.sub(r'^[^\w\s]*', '', keyword_final).strip()

            # 4. 허용된 문자(영어, 숫자, 공백, 하이픈, 슬래시) 외 모두 제거
            keyword_final = re.sub(r'[^a-zA-Z0-9\s\-/]', '', keyword_final).strip()

            # 5. 마지막에 남을 수 있는 콜론/점 제거
            keyword_final = re.sub(r'[:.]$', '', keyword_final).strip()

            if not keyword_final:
                logger.warning(f"⚠️ Global keyword parsing resulted in empty string: Original:'{line}', Candidate:'{keyword_raw}', Final:'{keyword_final}'")
                continue 

            if keyword_final and 2 <= len(keyword_final) <= 30: # 키워드 길이 제한 추가
                keywords.append({
                    "keyword": keyword_final,
                    "reason": reason,
                    "count": 30 - (len(keywords) * 5),
                    "rank": len(keywords) + 1
                })
                if len(keywords) >= 5: # 유효한 키워드가 5개 모이면 루프 종료
                    break
            else:
                logger.warning(f"⚠️ Invalid global keyword parsed: Original:'{line}', Candidate:'{keyword_raw}', Final:'{keyword_final}' (Length/Condition failed)")
        
        # 유효한 키워드가 부족할 때만 샘플 키워드를 사용합니다.
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

# 4단계: 해외 키워드로 관련 기사 검색
@retry_on_exception(max_retries=3, delay=0.5, backoff=2, allowed_exceptions=(requests.RequestException,))
async def search_global_keyword_articles(keyword: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """특정 키워드로 DeepSearch Global API에서 해외 관련 기사들을 검색합니다"""
    if not DEEPSEARCH_API_KEY:
        logger.error("❌ DeepSearch API 키가 설정되지 않음")
        return []
    
    try:
        # 해외 키워드 검색을 위한 URL 구성
        base_url = DEEPSEARCH_GLOBAL_KEYWORD_URL
        params = {
            "api_key": DEEPSEARCH_API_KEY,
            "keyword": keyword,  # 영어 키워드로 검색
            "date_from": start_date,
            "date_to": end_date,
            "page_size": 50  # 충분한 기사 수집
        }
        
        logger.info(f"🌍 해외 키워드 '{keyword}' 기사 검색 중... URL: {base_url}")
        logger.info(f"🌍 파라미터: {params}")
        response = requests.get(base_url, params=params, timeout=15) # 5초 -> 15초로 수정
        logger.info(f"🌍 응답 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ 해외 키워드 검색 API 호출 실패: {response.status_code}")
            logger.error(f"❌ 응답 내용: {response.text}")
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
            logger.warning(f"알 수 없는 해외 키워드 검색 응답 구조: {list(data.keys())}")
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
                "url": article.get("content_url", "") or article.get("url", ""),
                "date": formatted_date,
                "published_at": published_at,
                "source": "해외",
                "keyword": keyword,
                "region": "global",
                "relevance_score": calculate_relevance_score(article, keyword)
            }
            
            # 캐시에 저장 (URL 리다이렉트용)
            articles_cache[article_id] = processed_article
            processed_articles.append(processed_article)
        
        # 관련성 점수 기준으로 정렬
        processed_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"✅ 해외 키워드 '{keyword}' 관련 기사 {len(processed_articles)}개 검색 완료")
        return processed_articles[:15]  # 상위 15개만 반환
        
    except Exception as e:
        logger.error(f"❌ 해외 키워드 '{keyword}' 검색 오류: {e}", exc_info=True)
        return []

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
            "page_size": 50  # 15개에서 50개로 증가하여 더 많은 관련 기사 수집
        }
        
        logger.info(f"🔍 키워드 '{keyword}' 기사 검색 중... URL: {base_url}")
        logger.info(f"🔍 파라미터: {params}")
        response = requests.get(base_url, params=params, timeout=15)  # 3초->15초 수정
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
            "page_size": 50  # 15개에서 50개로 증가하여 더 많은 해외 기사 수집
        }
        
        logger.info(f"🔍 해외 키워드 '{keyword}' 검색...")
        response = requests.get(base_url, params=params, timeout=15)  # 5->15초 타임아웃
        
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
                article_id = generate_article_id(item)
                source_url = item.get("content_url", "") or item.get("url", "")
                
                article = {
                    "id": article_id,
                    "title": title,
                    "content": content,
                    "date": article_date,
                    "source_url": source_url,
                    "url": source_url,  # 프론트엔드에서 사용하는 필드
                    "keyword": keyword,
                    "source": "해외"
                }
                
                # 해외 기사도 캐시에 저장하여 원본 URL 리다이렉트 가능하게 함
                articles_cache[article_id] = article
                
                articles.append(article)
                
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
    response = requests.get(url, params=params, timeout=15) #5 -> 15초로 수정
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
                response = requests.get(base_url, params=params, timeout=15) # 5초 -> 15초로 수정
                
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
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "뉴스 키워드 분석 전문가입니다. 기사에서 중요한 키워드를 추출합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
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
            answer = await generate_keyword_trend_answer(question, keyword_info["keyword"])
        elif keyword_info["type"] == "comparison":
            answer = await generate_comparison_answer(question, keyword_info["keywords"])
        else:
            answer = await generate_contextual_answer(question, current_keywords)

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

async def generate_industry_based_answer(question, keyword, industry, current_keywords, reason: Optional[str] = None): # ✅ reason 파라미터 추가
    """산업별/직무별 관점 분석 기반 답변 생성"""
    try:
        # industry_context 맵은 기존과 동일 (주요 산업 분야만 포함)
        industry_context = {
            "사회": "사회적 영향, 정책적 측면, 시민 생활 변화",
            "경제": "경제적 파급효과, 시장 동향, 투자 관점",
            "IT/과학": "기술적 혁신, 연구개발 동향, 기술적 과제",
            "생활/문화": "일상생활 변화, 문화적 수용성, 소비자 행동",
            "세계": "글로벌 트렌드, 국제 경쟁, 해외 동향"
        }
        # 'industry' 파라미터가 '데이터 과학자' 같은 직무명일 수도 있으므로, 이를 관점으로 사용
        context_desc = industry_context.get(industry, f"'{industry}' 관점") # 리스트에 없는 관점일 경우 일반화

        # 프롬프트 조정: 'industry'를 '분석 관점'으로 명확히 지시
        reason_text = f"이 키워드는 '{reason}'이라는 이유로 주목받고 있습니다." if reason else "" # ✅ 이 줄 추가
        prompt = f"""
        다음은 사용자의 질문과 분석 대상 키워드, 그리고 분석 관점 직무/산업에 대한 정보입니다.
        이 정보를 바탕으로 '{industry}' 관점에서 '{keyword}'에 대해 구체적이고 전문적인 분석을 제공해주세요.
        {reason_text} # ✅ 이유 정보 포함
        특히 '{industry}' 직무/산업과 '{keyword}' 키워드의 연관성을 중점적으로 다루고, 현재 주간 핵심 키워드({', '.join(current_keywords)})도 고려하여 답변을 구성해주세요.

        질문: {question}
        분석 대상 키워드: {keyword}
        분석 관점 직무/산업: {industry} ({context_desc})

        답변 형식:
        · '{industry}' 관점에서 본 '{keyword}'의 현재 상황
        · 주요 동향과 변화
        · 전망과 시사점

        마크다운 헤더(#) 사용 금지. 중간점(·)과 이모지로 구분하세요.
        """

        completion = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                # system 프롬프트도 'industry'를 '분석 관점'으로 명확히 지시
                {"role": "system", "content": f"당신은 '{industry}' 관점에서 뉴스 데이터를 분석하고 키워드에 대해 전문적으로 답변하는 AI입니다. 마크다운 헤더(#) 사용 금지. 중간점(·)과 이모지만 사용하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=16384,
            temperature=0.3 # 일관성을 위해 0.3으로 조정 (원래 0.2였음)
        )

        return completion.choices[0].message.content

    except Exception as e:
        logger.error(f"죄송합니다. {industry} 관점에서의 '{keyword}' 분석 중 오류가 발생했습니다: {e}", exc_info=True)
        return f"죄송합니다. {industry} 관점에서의 '{keyword}' 분석 중 오류가 발생했습니다."

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

async def generate_comparison_answer(question, keywords, perspective_role: Optional[str] = None, reason: Optional[str] = None): # ✅ reason 파라미터 추가
    """키워드들을 비교 분석 답변 생성 (직무/산업 관점 포함)"""
    try:
        # 프롬프트에 직무/산업 관점 추가
        role_context = ""
        if perspective_role:
            role_context = f"'{perspective_role}'의 관점에서 "

        reason_text = f"주요 키워드 중 하나인 '{keywords[0]}'은(는) '{reason}'이라는 이유로 선정되었습니다." if reason and keywords else "" # ✅ 이 줄 추가
        prompt = f"""
        질문: {question}
        비교 대상: {', '.join(keywords)}
        분석 관점: {role_context}
        {reason_text} # ✅ 이유 정보 포함

        {role_context}'{', '.join(keywords)}' 키워드들을 비교 분석해주세요.

        비교 분석 내용:
        · 각 키워드의 현재 상황과 특징
        · 공통점과 차이점
        · 상호 관계와 영향
        · 각각의 전망과 중요성

        마크다운 헤더(#) 사용 금지. 중간점(·)과 이모지로 구분하세요.
        객관적이고 균형잡힌 시각으로 비교해주세요.
        """

        completion = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": f"당신은 {perspective_role or '기술'} 분야의 전문가로서 다양한 키워드를 비교 분석합니다. 객관적이고 균형잡힌 시각으로 답변합니다. 마크다운 헤더(#) 사용 금지. 중간점(·)과 이모지만 사용하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=16384
        )

        return completion.choices[0].message.content

    except Exception as e:
        logger.error(f"죄송합니다. 키워드 비교 분석 중 오류가 발생했습니다: {str(e)}")
        return f"죄송합니다. 키워드 비교 분석 중 오류가 발생했습니다: {str(e)}"

async def generate_contextual_answer(question, current_keywords):
    """현재 키워드 컨텍스트 기반 일반 답변 생성"""
    try:
        # 현재 주간 키워드 컨텍스트 추가
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

@app.get("/weekly-keywords-by-date")
async def get_weekly_keywords_by_date(start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
                               end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")):
    """국내 날짜별 주간 키워드 반환 (프론트에서 요청하는 엔드포인트) - 캐싱 적용"""
    region = "domestic" # 이 엔드포인트는 국내 전용이므로 'domestic'으로 고정

    # 1. 캐시 키 생성
    cache_key = f"{region}_{start_date}_{end_date}"
    
    # 2. 캐시 조회 시도
    cached_result = get_cache(cache_key)

    # 3. 캐시된 결과가 유효하면 즉시 반환
    if cached_result:
        logger.info(f"✅ 캐시된 국내 키워드 결과 사용: {cache_key}")
        return JSONResponse(content={
            "keywords": cached_result,
            "date_range": f"{start_date} ~ {end_date}",
            "total_count": len(cached_result),
            "tech_articles_count": 0, # 캐시된 데이터에서는 원본 기사 수를 알 수 없으므로 0 (또는 별도 캐시 필요)
            "region": region,
            "status": "success",
            "cached": True # 캐시 사용 여부를 클라이언트에 알림
        }, media_type="application/json; charset=utf-8")

    # 4. 캐시된 결과가 없으면 실제 데이터 수집 및 GPT 호출
    try:
        logger.info(f"📅 날짜별 국내 키워드 요청 (DeepSearch & GPT): {start_date} ~ {end_date}")
        
        # DeepSearch Tech에서 기사 수집
        tech_articles = await fetch_tech_articles(start_date, end_date)
        tech_articles_count = len(tech_articles)

        if not tech_articles:
            logger.warning(f"❌ 국내 Tech 기사 없음: {start_date} ~ {end_date}, 샘플 데이터 사용")
            keywords = get_sample_keywords_by_date(start_date, end_date)
        else:
            # GPT로 키워드 추출
            extracted_keywords = await extract_keywords_with_gpt(tech_articles)
            if extracted_keywords:
                keywords = extracted_keywords[:5]  # Top 5로 제한
            else:
                logger.warning("❌ 국내 GPT 키워드 추출 실패, 샘플 데이터 사용")
                keywords = get_sample_keywords_by_date(start_date, end_date)
        
        # 5. 추출된 키워드를 캐시에 저장
        set_cache(cache_key, keywords)

        # 응답 형식을 프론트 요구사항에 맞게 조정
        response_data = {
            "keywords": keywords,
            "date_range": f"{start_date} ~ {end_date}",
            "total_count": len(keywords),
            "tech_articles_count": tech_articles_count,
            "region": region,
            "status": "success",
            "cached": False # 캐시되지 않은 새 데이터임을 클라이언트에 알림
        }
        return JSONResponse(content=response_data, media_type="application/json; charset=utf-8")
    except Exception as e:
        logger.error(f"날짜별 국내 키워드 요청 오류: {e}", exc_info=True)
        # 오류 발생 시 샘플 키워드 반환 및 오류 메시지 포함
        keywords_on_error = get_sample_keywords_by_date(start_date, end_date)
        return JSONResponse(status_code=500, content={
            "error": str(e),
            "keywords": keywords_on_error, # 오류 시 샘플 키워드 반환
            "date_range": f"{start_date} ~ {end_date}",
            "region": region,
            "status": "error",
            "cached": False,
            "note": "오류로 인해 샘플 데이터가 반환되었습니다."
        })


@app.get("/global-weekly-keywords-by-date")
async def get_global_weekly_keywords_by_date(start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"), 
                               end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")):
    """해외 날짜별 주간 키워드 반환 (프론트에서 요청하는 엔드포인트) - 캐싱 적용"""
    region = "global" # 이 엔드포인트는 해외 전용이므로 'global'로 고정

    # 1. 캐시 키 생성
    cache_key = f"{region}_{start_date}_{end_date}"
    
    # 2. 캐시 조회 시도
    cached_result = get_cache(cache_key)

    # 3. 캐시된 결과가 유효하면 즉시 반환
    if cached_result:
        logger.info(f"✅ 캐시된 해외 키워드 결과 사용: {cache_key}")
        return JSONResponse(content={
            "keywords": cached_result,
            "date_range": f"{start_date} ~ {end_date}",
            "total_count": len(cached_result),
            "global_tech_articles_count": 0, # 캐시된 데이터에서는 원본 기사 수를 알 수 없으므로 0
            "region": region,
            "status": "success",
            "cached": True # 캐시 사용 여부를 클라이언트에 알림
        }, media_type="application/json; charset=utf-8")

    # 4. 캐시된 결과가 없으면 실제 데이터 수집 및 GPT 호출
    try:
        logger.info(f"🌍 해외 날짜별 키워드 요청 (DeepSearch & GPT): {start_date} ~ {end_date}")
        
        # 해외 Tech 기사 → 해외 전용 GPT 키워드 추출 워크플로우 사용
        global_tech_articles = await fetch_global_tech_articles(start_date, end_date)
        global_tech_articles_count = len(global_tech_articles)

        if not global_tech_articles:
            logger.warning(f"❌ 해외 Tech 기사 없음: {start_date} ~ {end_date}, 샘플 데이터 사용")
            # 해외 샘플 키워드 반환
            keywords = get_global_sample_keywords_by_date(start_date, end_date)
        else:
            # 해외 전용 GPT로 영어 키워드 추출
            extracted_keywords = await extract_global_keywords_with_gpt(global_tech_articles)
            if extracted_keywords:
                keywords = extracted_keywords[:5]  # Top 5로 제한
            else:
                logger.warning("❌ 해외 GPT 키워드 추출 실패, 샘플 데이터 사용")
                keywords = get_global_sample_keywords_by_date(start_date, end_date)
        
        # 5. 추출된 키워드를 캐시에 저장
        set_cache(cache_key, keywords)

        # 응답 형식을 프론트 요구사항에 맞게 조정 (키워드 배열로 반환)
        response_data = {
            "keywords": keywords,
            "date_range": f"{start_date} ~ {end_date}",
            "total_count": len(keywords),
            "global_tech_articles_count": global_tech_articles_count,
            "region": region,
            "status": "success",
            "cached": False # 캐시되지 않은 새 데이터임을 클라이언트에 알림
        }
        return JSONResponse(content=response_data, media_type="application/json; charset=utf-8")
    except Exception as e:
        logger.error(f"해외 날짜별 키워드 요청 오류: {e}", exc_info=True)
        # 오류 발생 시 샘플 키워드 반환 및 오류 메시지 포함
        keywords_on_error = get_global_sample_keywords_by_date(start_date, end_date)
        return JSONResponse(status_code=500, content={
            "error": str(e),
            "keywords": keywords_on_error, # 오류 시 샘플 키워드 반환
            "date_range": f"{start_date} ~ {end_date}",
            "region": region,
            "status": "error",
            "cached": False,
            "note": "오류로 인해 샘플 데이터가 반환되었습니다."
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
    """날짜에 따른 샘플 키워드 반환 (reason 포함)"""
    # 각 키워드에 임시 reason과 count를 부여합니다.
    default_reason = "API 호출 실패로 인한 샘플 데이터"

    if "07-01" in start_date:  # 7월 1주차
        return [
            {"keyword": "전기차", "count": 250, "rank": 1, "reason": "최근 전기차 판매 증가 및 정책 지원"},
            {"keyword": "배터리", "count": 230, "rank": 2, "reason": "차세대 배터리 기술 개발 경쟁 심화"},
            {"keyword": "충전인프라", "count": 210, "rank": 3, "reason": "전기차 충전 인프라 확충 요구 증대"},
            {"keyword": "자율주행", "count": 190, "rank": 4, "reason": "자율주행 기술 상용화 논의 활발"},
            {"keyword": "테슬라", "count": 170, "rank": 5, "reason": "테슬라 신모델 출시 및 시장 영향력"},
        ]
    elif "07-06" in start_date:  # 7월 2주차  
        return [
            {"keyword": "메타버스", "count": 250, "rank": 1, "reason": "가상현실 기술의 발전과 엔터테인먼트 산업 적용"},
            {"keyword": "VR", "count": 230, "rank": 2, "reason": "VR 기기 보급 확대 및 콘텐츠 다양화"},
            {"keyword": "가상현실", "count": 210, "rank": 3, "reason": "가상현실 기술의 산업 활용 분야 확대"},
            {"keyword": "AR", "count": 190, "rank": 4, "reason": "증강현실 기술의 일상생활 적용"},
            {"keyword": "NFT", "count": 170, "rank": 5, "reason": "디지털 자산 시장의 새로운 트렌드"},
        ]
    elif "07-14" in start_date:  # 7월 3주차
        return [
            {"keyword": "인공지능", "count": 250, "rank": 1, "reason": "AI 기술의 범용화 및 다양한 산업 적용"},
            {"keyword": "AI", "count": 230, "rank": 2, "reason": "AI 모델 고도화 및 학습 데이터 중요성"},
            {"keyword": "ChatGPT", "count": 210, "rank": 3, "reason": "대화형 AI의 발전과 서비스 확산"},
            {"keyword": "머신러닝", "count": 190, "rank": 4, "reason": "데이터 기반의 예측 및 분석 능력 향상"},
            {"keyword": "딥러닝", "count": 170, "rank": 5, "reason": "복잡한 문제 해결을 위한 딥러닝 알고리즘 활용"},
        ]
    else:
        return [
            {"keyword": "기술", "count": 250, "rank": 1, "reason": default_reason},
            {"keyword": "혁신", "count": 230, "rank": 2, "reason": default_reason},
            {"keyword": "디지털", "count": 210, "rank": 3, "reason": default_reason},
            {"keyword": "정보", "count": 190, "rank": 4, "reason": default_reason},
            {"keyword": "시스템", "count": 170, "rank": 5, "reason": default_reason}
        ]


@app.post("/industry-analysis")
async def get_industry_analysis(request: IndustryKeywordAnalysisRequest): # 파라미터 변경
    """산업별 키워드 분석 (이제 직무 관점도 포함)"""
    industry_perspective = request.industry_perspective # '데이터 과학자' 같은 직무/산업 관점
    target_keyword = request.target_keyword           # '인공지능' 같은 실제 분석 대상 키워드

    if not industry_perspective or not target_keyword:
        raise HTTPException(status_code=400, detail="분석 관점과 키워드를 모두 제공해야 합니다.")

    logger.info(f"📊 산업별/직무 관점 분석 요청: 관점='{industry_perspective}', 키워드='{target_keyword}'")

    try:
        # 긍정적/일반 분석 생성
        main_completion_content = await generate_industry_based_answer( # 함수는 기존 그대로 사용
            question=f"'{target_keyword}'에 대한 '{industry_perspective}' 직무/산업 관점에서의 긍정적 분석",
            keyword=target_keyword,
            industry=industry_perspective, # industry_context를 위해 perspective를 industry로 전달
            current_keywords=[target_keyword] # 컨텍스트에 대상 키워드 전달
        )

        # 비판적/회의적 분석 생성
        counter_completion_content = await generate_comparison_answer( # 함수는 기존 그대로 사용
            question=f"'{target_keyword}'에 대한 '{industry_perspective}' 직무/산업 관점에서의 비판적 분석",
            keywords=[target_keyword], # 비교 키워드로 대상 키워드 전달
        )

        return {
            "analysis": main_completion_content,
            "counter_analysis": counter_completion_content
        }
    except Exception as e:
        logger.error(f"❌ 산업별/직무 관점 분석 엔드포인트 오류: {e}", exc_info=True)
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
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "당신은 IT/기술 뉴스 분석 전문가입니다. 사용자의 질문에 간결하고 정확하게 답변해주세요."},
                    {"role": "user", "content": question}
                ],
                max_tokens=16384,
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

# =============================================================================
# 이메일 구독 기능
# =============================================================================

# 간단한 구독자 저장 (JSON 파일 사용)
SUBSCRIBERS_FILE = "subscribers.json"

def load_subscribers():
    """구독자 목록 로드"""
    try:
        if os.path.exists(SUBSCRIBERS_FILE):
            with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"구독자 로드 오류: {e}")
        return []

def save_subscribers(subscribers):
    """구독자 목록 저장"""
    try:
        with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(subscribers, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"구독자 저장 오류: {e}")
        return False

@app.post("/api/subscribe")
async def subscribe_email(subscription: SubscriptionRequest):
    """이메일 구독 API"""
    try:
        email = subscription.email
        
        # 기존 구독자 확인
        subscribers = load_subscribers()
        
        # 이미 구독된 이메일인지 확인
        for subscriber in subscribers:
            if subscriber.get("email") == email:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "이미 구독된 이메일입니다."}
                )
        
        # 새 구독자 추가
        new_subscriber = {
            "email": email,
            "subscribed_at": datetime.now().isoformat(),
            "active": True
        }
        
        subscribers.append(new_subscriber)
        
        if save_subscribers(subscribers):
            logger.info(f"✅ 새 구독자 추가: {email}")
            return JSONResponse(
                status_code=200,
                content={
                    "message": "구독이 완료되었습니다!",
                    "email": email
                }
            )
        else:
            raise HTTPException(status_code=500, detail="구독 저장 중 오류가 발생했습니다.")
            
    except Exception as e:
        logger.error(f"❌ 구독 오류: {e}")
        raise HTTPException(status_code=500, detail=f"구독 처리 중 오류: {str(e)}")

@app.get("/api/subscribers")
async def get_subscribers():
    """구독자 목록 조회 API"""
    try:
        subscribers = load_subscribers()
        return JSONResponse(
            status_code=200,
            content=subscribers
        )
    except Exception as e:
        logger.error(f"❌ 구독자 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"구독자 목록 조회 중 오류: {str(e)}")

@app.post("/api/send-insights")
async def send_weekly_insights(request: EmailInsightRequest):
    """주간 인사이트 이메일 발송 API (수동 발송용)"""
    try:
        # 이메일 설정 확인
        if not EMAIL_USER or not EMAIL_PASSWORD:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "이메일 설정이 필요합니다",
                    "detail": ".env 파일에 EMAIL_USER와 EMAIL_PASSWORD를 설정해주세요.",
                    "instruction": "Gmail 앱 비밀번호 설정 후 .env 파일을 업데이트하세요."
                }
            )
        
        email = request.email
        
        # 주간 키워드 가져오기
        keywords_data = await get_weekly_keywords_data()
        
        # 인사이트 생성
        insight_content = await generate_weekly_insight(keywords_data)
        
        # 이메일 발송
        success = await send_email(email, "📊 주간 AI 뉴스 인사이트", insight_content)
        
        if success:
            return JSONResponse(
                status_code=200,
                content={"message": f"인사이트가 {email}로 발송되었습니다."}
            )
        else:
            raise HTTPException(status_code=500, detail="이메일 발송 실패")
            
    except Exception as e:
        logger.error(f"❌ 인사이트 발송 오류: {e}")
        raise HTTPException(status_code=500, detail=f"발송 중 오류: {str(e)}")

@app.post("/api/send-to-all-subscribers")
async def send_to_all_subscribers():
    """모든 구독자에게 주간 인사이트 발송"""
    try:
        subscribers = load_subscribers()
        active_subscribers = [s for s in subscribers if s.get("active", True)]
        
        if not active_subscribers:
            return JSONResponse(
                status_code=200,
                content={"message": "활성 구독자가 없습니다.", "sent_count": 0}
            )
        
        # 주간 키워드 및 인사이트 생성
        keywords_data = await get_weekly_keywords_data()
        insight_content = await generate_weekly_insight(keywords_data)
        
        sent_count = 0
        failed_count = 0
        
        for subscriber in active_subscribers:
            email = subscriber.get("email")
            try:
                success = await send_email(email, "📊 주간 AI 뉴스 인사이트", insight_content)
                if success:
                    sent_count += 1
                    logger.info(f"✅ 발송 성공: {email}")
                else:
                    failed_count += 1
                    logger.warning(f"❌ 발송 실패: {email}")
                    
                # 발송 간격 (Gmail 제한 고려)
                await asyncio.sleep(1)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ {email} 발송 오류: {e}")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"발송 완료: 성공 {sent_count}건, 실패 {failed_count}건",
                "sent_count": sent_count,
                "failed_count": failed_count,
                "total_subscribers": len(active_subscribers)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ 전체 발송 오류: {e}")
        raise HTTPException(status_code=500, detail=f"전체 발송 중 오류: {str(e)}")

async def get_weekly_keywords_data():
    """주간 키워드 데이터 수집"""
    try:
        # 현재 주차 키워드 가져오기
        start_date = "2025-07-14"
        end_date = "2025-07-21"
        
        # 국내 키워드
        domestic_articles = await fetch_tech_articles(start_date, end_date)
        domestic_keywords = await extract_keywords_with_gpt(domestic_articles)
        
        # 해외 키워드
        global_articles = await fetch_global_tech_articles(start_date, end_date)
        global_keywords = await extract_global_keywords_with_gpt(global_articles)
        
        return {
            "domestic_keywords": domestic_keywords[:5],
            "global_keywords": global_keywords[:5],
            "period": f"{start_date} ~ {end_date}"
        }
    except Exception as e:
        logger.error(f"키워드 데이터 수집 오류: {e}")
        return {
            "domestic_keywords": [
                {"keyword": "인공지능", "count": 25, "rank": 1},
                {"keyword": "반도체", "count": 20, "rank": 2}
            ],
            "global_keywords": [
                {"keyword": "AI Technology", "count": 30, "rank": 1},
                {"keyword": "Innovation", "count": 25, "rank": 2}
            ],
            "period": f"{start_date} ~ {end_date}"
        }

async def generate_weekly_insight(keywords_data):
    """주간 인사이트 생성 (개선된 구조)"""
    try:
        domestic_keywords = [k["keyword"] for k in keywords_data["domestic_keywords"]]
        global_keywords = [k["keyword"] for k in keywords_data["global_keywords"]]
        
        # 키워드 카운트 정보 포함
        domestic_details = [f"{k['keyword']} ({k['count']}건)" for k in keywords_data["domestic_keywords"][:3]]
        global_details = [f"{k['keyword']} ({k['count']}건)" for k in keywords_data["global_keywords"][:3]]
        
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
        
        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "당신은 AI 뉴스 분석 전문가입니다. 주간 인사이트를 구독자들에게 제공합니다. 마크다운 헤더(#) 절대 사용 금지. 대신 이모지와 중간점(·)만 사용하여 구분하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"인사이트 생성 오류: {e}")
        return f"""
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

async def send_email(to_email: str, subject: str, content: str):
    """실제 이메일 발송 함수 (Gmail SMTP)"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            logger.error("이메일 설정이 없습니다. EMAIL_USER, EMAIL_PASSWORD 환경변수를 확인하세요.")
            return False
        
        # HTML 이메일 생성
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        
        # 개선된 HTML 템플릿
        html_body = content.replace('\n', '<br>')
        html_content = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #1C2039, #00D9C0); padding: 25px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 22px;">🚀 News GPT v2</h1>
                    <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0; font-size: 13px;">AI 뉴스 키워드 분석 주간 인사이트</p>
                </div>
                <div style="padding: 25px;">
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #00D9C0;">
                        {html_body}
                    </div>
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="http://localhost:8000" style="display: inline-block; background: #00D9C0; color: white; padding: 10px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">📊 자세한 분석 보기</a>
                    </div>
                </div>
                <div style="background: #f8f9fa; padding: 15px; text-align: center; border-top: 1px solid #eee;">
                    <p style="color: #666; font-size: 12px; margin: 0;">구독 해지: 이 메일에 회신 | <a href="http://localhost:8000" style="color: #00D9C0;">웹사이트 방문</a></p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # SMTP 발송
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ 실제 이메일 발송 성공: {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 이메일 발송 실패 ({to_email}): {e}")
        return False
    

@app.get("/api/trending")
def get_trending_keywords(country_codes: List[str] = Query(...)):
    global CACHE_GOOGLE_TRENDING_KEYWORDS

    try:
        if CACHE_GOOGLE_TRENDING_KEYWORDS is None:
            cache_google_tranding(country_codes)

        return CACHE_GOOGLE_TRENDING_KEYWORDS

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

def find_shared_keywords_with_llm(raw_keywords):
    """LLM을 사용하여 여러 국가 간 동일 의미 키워드 찾기"""
    try:
        # 키워드를 LLM이 이해하기 쉬운 형태로 포맷팅
        formatted_keywords = []
        for i, item in enumerate(raw_keywords):
            formatted_keywords.append(f"{i}: '{item['keyword']}' ({item['country']})")
        
        keywords_text = "\n".join(formatted_keywords)
        
        prompt = f"""다음은 국가별 트렌딩 키워드입니다. 
**여러 국가에서 동시에 나타나는 동일한 의미의 키워드 그룹**을 찾아주세요.

키워드 목록:
{keywords_text}

조건:
- 같은 국가 내의 키워드는 비교하지 마세요
- 다른 국가 간에 의미적으로 동일한 키워드만 찾아주세요  
- Tesla/TSLA/테슬라, iPhone/아이폰, Trump/트럼프 같은 경우가 좋은 예시입니다
- 단순히 비슷한 주제가 아닌, 정확히 같은 대상을 가리키는 키워드만 묶어주세요

응답 형식 (JSON만): {{"shared_groups": [[인덱스1, 인덱스2], [인덱스3, 인덱스4, 인덱스5]]}}
예시: {{"shared_groups": [[0, 5, 12], [3, 8]]}}"""

        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # 낮은 temperature로 일관성 확보
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # JSON 파싱 시도
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result_json = json.loads(json_match.group())
            shared_groups = result_json.get('shared_groups', [])
            
            # shared_indices 계산
            shared_indices = set()
            for group in shared_groups:
                # 그룹이 실제로 여러 국가를 포함하는지 확인
                countries_in_group = set()
                for idx in group:
                    if 0 <= idx < len(raw_keywords):
                        countries_in_group.add(raw_keywords[idx]['country'])
                
                # 여러 국가에 걸쳐 있는 그룹만 공통 키워드로 처리
                if len(countries_in_group) > 1:
                    shared_indices.update(group)
            
            return shared_indices
        else:
            print("LLM 응답에서 JSON을 찾을 수 없음")
            return set()
            
    except Exception as e:
        print(f"LLM 키워드 매칭 실패: {e}")
        # 실패 시 기존 임베딩 방식으로 폴백
        return find_shared_keywords_with_embedding(raw_keywords)

def find_shared_keywords_with_embedding(raw_keywords):
    """기존 임베딩 방식 (폴백용)"""
    try:
        texts_for_embedding = []
        for item in raw_keywords:
            kw = item["keyword"]
            if item["country"] in ["KR", "MX"]:
                try:
                    kw_en = translator.translate(kw, dest='en').text
                except Exception:
                    kw_en = kw
            else:
                kw_en = kw
            item["keyword_en"] = kw_en
            texts_for_embedding.append(kw_en)

        embeddings = sentence_transformer_model.encode(texts_for_embedding)
        shared_indices = set()
        countries = [item['country'] for item in raw_keywords]

        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                if countries[i] != countries[j] and cosine_similarity([embeddings[i]], [embeddings[j]])[0][0] >= 0.65:
                    shared_indices.add(i)
                    shared_indices.add(j)
        
        return shared_indices
    except Exception as e:
        print(f"임베딩 방식도 실패: {e}")
        return set()


@app.get("/api/news")
def get_news(country: str, keyword: str):
    try:
        encoded_kw = urllib.parse.quote(keyword)
        hl_map = {'US': 'en', 'GB': 'en-GB', 'MX': 'es-419', 'KR': 'ko', 'IN': 'en-IN', 'ZA': 'en-ZA', 'AU': 'en-AU'}
        hl = hl_map.get(country, 'en')
        ceid = f"{country}:{hl}"
        rss_url = f"https://news.google.com/rss/search?q={encoded_kw}&hl={hl}&gl={country}&ceid={ceid}"
        feed = feedparser.parse(rss_url)
        articles = []

        for entry in feed.entries:
            published_str = getattr(entry, 'published', '')
            try:
                published_dt = date_parser.parse(published_str)
            except Exception:
                published_dt = datetime.min
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "published": published_str,
                "published_dt": published_dt
            })

        sorted_articles = sorted(articles, key=lambda x: x['published_dt'], reverse=True)[:10]
        for article in sorted_articles:
            article.pop('published_dt', None)

        return {"news": sorted_articles, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"뉴스 가져오기 실패: {str(e)}")

@app.post("/api/gpt-commentary")
def generate_commentary(req: TrendRequest):
    try:
        if not req.headlines:
            return {"comment": "관련 뉴스가 없어 트렌드 해설을 제공할 수 없습니다.", "status": "no_news"}

        prompt = (
            f"The following are recent news headlines related to the keyword '{req.keyword}':\n"
            + "\n".join(f"- {title}" for title in req.headlines)
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

        return {"comment": response.choices[0].message.content, "status": "success"}

    except Exception as e:
        return {
            "comment": f"GPT 응답 오류: {str(e)}",
            "status": "error",
            "error": str(e)
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
    logger.info("   4️⃣ 키워드트렌딩")
    logger.info("   5️⃣ 기사클릭 → URL리다이렉트")
    logger.info("🌐 서버 주소: http://localhost:8000")
    
    # FastAPI 서버 직접 실행
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)