import asyncio
import time
import hashlib
from functools import wraps
import logging
from typing import Dict, Any
import json
import os

logger = logging.getLogger(__name__)

# API 호출 재시도 데코레이터
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
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator

# --- 파일 기반 캐시로 변경 ---
CACHE_DIR = "cache_data"
CACHE_EXPIRY_SECONDS = 30 * 60  # 30분

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_cache_filepath(cache_key: str) -> str:
    """캐시 키에 해당하는 파일 경로를 반환합니다."""
    return os.path.join(CACHE_DIR, f"{cache_key}.json")

def set_cache(cache_key: str, data: Any):
    """데이터를 JSON 파일로 캐시에 저장합니다."""
    filepath = get_cache_filepath(cache_key)
    cache_content = {
        "timestamp": time.time(),
        "data": data
    }
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cache_content, f, ensure_ascii=False, indent=4)
        logger.info(f"💾 캐시 저장: {cache_key}")
    except Exception as e:
        logger.error(f"❌ 캐시 저장 실패 ({cache_key}): {e}")

def get_cache(cache_key: str) -> Any:
    """파일 캐시에서 데이터를 읽어옵니다."""
    filepath = get_cache_filepath(cache_key)
    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            cache_content = json.load(f)
        
        # 캐시 유효기간 확인
        cache_age = time.time() - cache_content.get("timestamp", 0)
        if cache_age > CACHE_EXPIRY_SECONDS:
            logger.info(f"⌛ 캐시 만료: {cache_key}")
            os.remove(filepath)  # 만료된 캐시 파일 삭제
            return None
            
        logger.info(f"⚡ 캐시 히트: {cache_key}")
        return cache_content.get("data")
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"❌ 캐시 읽기 실패 ({cache_key}): {e}")
        return None

# 기사 관련 유틸리티
def generate_article_id(article: Dict[str, Any]) -> str:
    content = f"{article.get('title', '')}{article.get('url', '')}{article.get('published_at', '')}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]

def calculate_relevance_score(article: Dict[str, Any], keyword: str) -> float:
    title = article.get("title", "").lower()
    content = article.get("summary", "") or article.get("content", "")
    content = content.lower()
    keyword_lower = keyword.lower()
    
    score = 0.0
    if keyword_lower in title:
        score += 10.0
    content_count = content.count(keyword_lower)
    score += content_count * 2.0
    pub_date = article.get("published_at", "")
    if "2025-07" in pub_date:
        score += 5.0
    return score 