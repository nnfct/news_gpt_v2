import logging
from typing import List
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.deepsearch_service import search_articles_by_keyword, search_global_keyword_articles, collect_it_news_from_deepsearch, fetch_tech_articles, fetch_global_tech_articles
from services.openai_service import extract_keywords_with_gpt, extract_global_keywords_with_gpt, extract_keywords_with_gpt4o, analyze_keyword_dynamically
from services.sample_service import get_sample_keywords_by_date, get_global_sample_keywords_by_date
from utils.helpers import get_cache, set_cache
from services.trending_service import get_news

logger = logging.getLogger(__name__)
router = APIRouter()

TRENDING_CACHE_KEY = "google_trending_keywords"

@router.get("/keyword-articles/{keyword}")
async def get_keyword_articles(keyword: str, 
                              start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
                              end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")):
    """키워드 클릭시 관련 기사들을 반환"""
    try:
        if keyword == "undefined" or not keyword or keyword.strip() == "":
            logger.warning(f"⚠️ 잘못된 키워드 '{keyword}' 요청 - 기본 키워드로 대체")
            keyword = "AI"
        
        logger.info(f"🔍 키워드 '{keyword}' 관련 기사 검색 - 기간: {start_date} ~ {end_date}")
        
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

@router.get("/keyword-articles")
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

@router.get("/global-keyword-articles/{keyword}")
async def get_global_keyword_articles(
    keyword: str, 
    start_date: str = Query("2025-07-14", description="시작일"),
    end_date: str = Query("2025-07-18", description="종료일")
):
    """해외 키워드별 관련 기사 검색 API"""
    try:
        logger.info(f"🌍 해외 키워드별 기사 검색: '{keyword}' ({start_date} ~ {end_date})")
        articles = await search_global_keyword_articles(keyword, start_date, end_date)
        
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

@router.get("/articles")
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

@router.get("/keywords")
async def get_weekly_keywords_endpoint(start_date: str = "2025-07-14", end_date: str = "2025-07-18"):
    """DeepSearch → GPT-4o → Top 5 키워드 반환"""
    try:
        logger.info(f"🚀 News GPT v2 분석 시작 - 기간: {start_date} ~ {end_date}")
        articles = await collect_it_news_from_deepsearch(start_date, end_date)
        if not articles:
            logger.warning("/api/keywords: 기사 없음")
            return {
                "error": "뉴스 수집 실패", 
                "keywords": [],
                "details": "DeepSearch API에서 기사를 가져올 수 없습니다."
            }
        logger.info(f"   ✅ {len(articles)}개 기사 수집 완료")
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
            "flow": "DeepSearch → GPT-4o",
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

@router.get("/weekly-keywords-by-date")
async def get_weekly_keywords_by_date(start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
                               end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")):
    """국내 날짜별 주간 키워드 반환 (프론트에서 요청하는 엔드포인트) - 캐싱 적용"""
    region = "domestic"
    cache_key = f"{region}_{start_date}_{end_date}"
    cached_result = get_cache(cache_key)

    if cached_result:
        logger.info(f"✅ 캐시된 국내 키워드 결과 사용: {cache_key}")
        return JSONResponse(content={
            "keywords": cached_result,
            "date_range": f"{start_date} ~ {end_date}",
            "total_count": len(cached_result),
            "tech_articles_count": 0,
            "region": region,
            "status": "success",
            "cached": True
        }, media_type="application/json; charset=utf-8")

    try:
        logger.info(f"📅 날짜별 국내 키워드 요청 (DeepSearch & GPT): {start_date} ~ {end_date}")
        tech_articles = await fetch_tech_articles(start_date, end_date)
        tech_articles_count = len(tech_articles)

        if not tech_articles:
            logger.warning(f"❌ 국내 Tech 기사 없음: {start_date} ~ {end_date}, 샘플 데이터 사용")
            keywords = get_sample_keywords_by_date(start_date, end_date)
        else:
            extracted_keywords = await extract_keywords_with_gpt(tech_articles)
            if extracted_keywords:
                keywords = extracted_keywords[:5]
            else:
                logger.warning("❌ 국내 GPT 키워드 추출 실패, 샘플 데이터 사용")
                keywords = get_sample_keywords_by_date(start_date, end_date)
        
        set_cache(cache_key, keywords)

        response_data = {
            "keywords": keywords,
            "date_range": f"{start_date} ~ {end_date}",
            "total_count": len(keywords),
            "tech_articles_count": tech_articles_count,
            "region": region,
            "status": "success",
            "cached": False
        }
        return JSONResponse(content=response_data, media_type="application/json; charset=utf-8")
    except Exception as e:
        logger.error(f"날짜별 국내 키워드 요청 오류: {e}", exc_info=True)
        keywords_on_error = get_sample_keywords_by_date(start_date, end_date)
        return JSONResponse(status_code=500, content={
            "error": str(e),
            "keywords": keywords_on_error,
            "date_range": f"{start_date} ~ {end_date}",
            "region": region,
            "status": "error",
            "cached": False,
            "note": "오류로 인해 샘플 데이터가 반환되었습니다."
        })

@router.get("/global-weekly-keywords-by-date")
async def get_global_weekly_keywords_by_date(start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"), 
                               end_date: str = Query(..., description="종료일 (YYYY-MM-DD)")):
    """해외 날짜별 주간 키워드 반환 (프론트에서 요청하는 엔드포인트) - 캐싱 적용"""
    region = "global"
    cache_key = f"{region}_{start_date}_{end_date}"
    cached_result = get_cache(cache_key)

    if cached_result:
        logger.info(f"✅ 캐시된 해외 키워드 결과 사용: {cache_key}")
        return JSONResponse(content={
            "keywords": cached_result,
            "date_range": f"{start_date} ~ {end_date}",
            "total_count": len(cached_result),
            "global_tech_articles_count": 0,
            "region": region,
            "status": "success",
            "cached": True
        }, media_type="application/json; charset=utf-8")

    try:
        logger.info(f"🌍 해외 날짜별 키워드 요청 (DeepSearch & GPT): {start_date} ~ {end_date}")
        global_tech_articles = await fetch_global_tech_articles(start_date, end_date)
        global_tech_articles_count = len(global_tech_articles)

        if not global_tech_articles:
            logger.warning(f"❌ 해외 Tech 기사 없음: {start_date} ~ {end_date}, 샘플 데이터 사용")
            keywords = get_global_sample_keywords_by_date(start_date, end_date)
        else:
            extracted_keywords = await extract_global_keywords_with_gpt(global_tech_articles)
            if extracted_keywords:
                keywords = extracted_keywords[:5]
            else:
                logger.warning("❌ 해외 GPT 키워드 추출 실패, 샘플 데이터 사용")
                keywords = get_global_sample_keywords_by_date(start_date, end_date)
        
        set_cache(cache_key, keywords)

        response_data = {
            "keywords": keywords,
            "date_range": f"{start_date} ~ {end_date}",
            "total_count": len(keywords),
            "global_tech_articles_count": global_tech_articles_count,
            "region": region,
            "status": "success",
            "cached": False
        }
        return JSONResponse(content=response_data, media_type="application/json; charset=utf-8")
    except Exception as e:
        logger.error(f"해외 날짜별 키워드 요청 오류: {e}", exc_info=True)
        keywords_on_error = get_global_sample_keywords_by_date(start_date, end_date)
        return JSONResponse(status_code=500, content={
            "error": str(e),
            "keywords": keywords_on_error,
            "date_range": f"{start_date} ~ {end_date}",
            "region": region,
            "status": "error",
            "cached": False,
            "note": "오류로 인해 샘플 데이터가 반환되었습니다."
        })

@router.get("/weekly-keywords")
def get_weekly_keywords():
    """주간 Top 3 키워드 반환"""
    try:
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

@router.post("/keyword-analysis")
def post_keyword_analysis(request: dict):
    """동적 키워드 분석 - 클릭된 키워드에 대한 다각도 분석"""
    return analyze_keyword_dynamically(request) 

@router.get("/trending")
def get_trending_keywords():
    """실시간 트렌딩 키워드 반환 (캐시된 데이터)"""
    cached_data = get_cache(TRENDING_CACHE_KEY)

    if cached_data:
        return JSONResponse(content=cached_data)
    else:
        return JSONResponse(content={"status": "caching", "data": []}, status_code=202)

@router.get("/news")
def get_news_endpoint(country: str, keyword: str):
    """특정 국가 및 키워드에 대한 뉴스 기사 반환"""
    try:
        articles = get_news(country, keyword)
        return JSONResponse(content={"news": articles})
    except Exception as e:
        logger.error(f"Error in /api/v1/news endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch news articles.")