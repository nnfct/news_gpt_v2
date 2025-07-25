import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler

from api.api_router import router as api_router
from services.trending_service import cache_google_tranding

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("news_gpt_v2")

@asynccontextmanager
async def lifespan(_: FastAPI):
    # 서버 시작 시 실행
    logger.info("🚀 서버 시작: 스케줄러를 가동합니다.")
    
    country_codes = ['KR', 'US', 'MX', 'GB', 'IN', 'ZA', 'AU']
    cache_google_tranding(country_codes)

    scheduler = BackgroundScheduler()
    scheduler.add_job(cache_google_tranding, trigger="cron", minute=0, args=[country_codes])
    scheduler.start()
    
    yield
    # 서버 종료 시 실행 (필요 시 추가)
    logger.info("✅ 서버 종료")

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="News GPT v2", 
    description="AI 뉴스 키워드 분석 플랫폼", 
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 페이지 제공
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

# API 라우터 포함
app.include_router(api_router)

# uvicorn 실행을 위한 설정 (터미널에서 직접 실행 시)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)