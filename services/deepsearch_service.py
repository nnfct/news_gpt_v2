import logging
import requests
from typing import List, Dict, Any

from utils.helpers import retry_on_exception, generate_article_id, calculate_relevance_score
from core.config import DEEPSEARCH_API_KEY, DEEPSEARCH_TECH_URL, DEEPSEARCH_GLOBAL_TECH_URL, DEEPSEARCH_GLOBAL_KEYWORD_URL, DEEPSEARCH_KEYWORD_URL

logger = logging.getLogger(__name__)

articles_cache = {}

@retry_on_exception(max_retries=1, delay=0.1, backoff=1.5, allowed_exceptions=(requests.RequestException,))
async def fetch_tech_articles(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """DeepSearch Tech 카테고리에서 기사들을 수집합니다 (빠른 처리)"""
    if not DEEPSEARCH_API_KEY:
        logger.error("❌ DeepSearch API 키가 설정되지 않음")
        return []
    
    try:
        base_url = DEEPSEARCH_TECH_URL
        params = {
            "api_key": DEEPSEARCH_API_KEY,
            "date_from": start_date,
            "date_to": end_date,
            "page_size": 50
        }
        
        logger.info(f"🚀 Tech 기사 수집 중...")
        response = requests.get(base_url, params=params, timeout=15)
        logger.info(f"📊 응답 상태: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ API 호출 실패: {response.status_code}")
            return []
            
        response.raise_for_status()
        data = response.json()
        
        articles = []
        if "articles" in data:
            articles = data["articles"]
        elif "data" in data:
            articles = data["data"]
        else:
            logger.warning(f"알 수 없는 응답 구조: {list(data.keys())}")
            return []
        
        processed_articles = []
        for article in articles:
            article_id = generate_article_id(article)
            
            published_at = article.get("published_at", "")
            formatted_date = "날짜 정보 없음"
            if published_at:
                try:
                    if "T" in published_at:
                        formatted_date = published_at.split("T")[0]
                    else:
                        formatted_date = published_at[:10]
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
            
            articles_cache[article_id] = processed_article
            processed_articles.append(processed_article)
        
        logger.info(f"✅ Tech 기사 {len(processed_articles)}개 수집 완료")
        return processed_articles
        
    except Exception as e:
        logger.error(f"❌ Tech 기사 수집 오류: {e}", exc_info=True)
        return []

@retry_on_exception(max_retries=1, delay=0.1, backoff=1.5, allowed_exceptions=(requests.RequestException,))
async def fetch_global_tech_articles(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """DeepSearch Global API에서 해외 Tech 기사들을 수집합니다 (빠른 처리)"""
    if not DEEPSEARCH_API_KEY:
        logger.error("❌ DeepSearch API 키가 설정되지 않음")
        return []
    
    try:
        base_url = DEEPSEARCH_GLOBAL_TECH_URL
        params = {
            "api_key": DEEPSEARCH_API_KEY,
            "keyword": "tech",
            "date_from": start_date,
            "date_to": end_date,
            "page_size": 50
        }
        
        logger.info(f"🌍 해외 Tech 기사 수집 중...")
        response = requests.get(base_url, params=params, timeout=15)
        logger.info(f"📊 해외 응답 상태: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ 해외 API 호출 실패: {response.status_code}")
            return []
            
        response.raise_for_status()
        data = response.json()
        
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
        
        processed_articles = []
        for article in articles:
            article_id = generate_article_id(article)
            
            published_at = article.get("published_at", "")
            formatted_date = "날짜 정보 없음"
            if published_at:
                try:
                    if "T" in published_at:
                        formatted_date = published_at.split("T")[0]
                    else:
                        formatted_date = published_at[:10]
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
            
            articles_cache[article_id] = processed_article
            processed_articles.append(processed_article)
        
        logger.info(f"✅ 해외 Tech 기사 {len(processed_articles)}개 수집 완료")
        return processed_articles
        
    except Exception as e:
        logger.error(f"❌ 해외 Tech 기사 수집 오류: {e}", exc_info=True)
        return []

@retry_on_exception(max_retries=3, delay=0.5, backoff=2, allowed_exceptions=(requests.RequestException,))
async def search_articles_by_keyword(keyword: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """특정 키워드로 DeepSearch에서 관련 기사들을 검색합니다"""
    if not DEEPSEARCH_API_KEY:
        logger.error("❌ DeepSearch API 키가 설정되지 않음")
        return []
    
    try:
        base_url = DEEPSEARCH_KEYWORD_URL
        params = {
            "api_key": DEEPSEARCH_API_KEY,
            "keyword": keyword,
            "date_from": start_date,
            "date_to": end_date,
            "page_size": 50
        }
        
        logger.info(f"🔍 키워드 '{keyword}' 기사 검색 중... URL: {base_url}")
        logger.info(f"🔍 파라미터: {params}")
        response = requests.get(base_url, params=params, timeout=15)
        logger.info(f"🔍 응답 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ 키워드 검색 API 호출 실패: {response.status_code}")
            logger.error(f"❌ 응답 내용: {response.text}")
            return []
            
        response.raise_for_status()
        data = response.json()
        
        articles = []
        if "articles" in data:
            articles = data["articles"]
        elif "data" in data:
            articles = data["data"]
        else:
            logger.warning(f"알 수 없는 키워드 검색 응답 구조: {list(data.keys())}")
            return []
        
        processed_articles = []
        for article in articles:
            article_id = generate_article_id(article)
            
            published_at = article.get("published_at", "")
            formatted_date = "날짜 정보 없음"
            if published_at:
                try:
                    if "T" in published_at:
                        formatted_date = published_at.split("T")[0]
                    else:
                        formatted_date = published_at[:10]
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
            
            articles_cache[article_id] = processed_article
            processed_articles.append(processed_article)
        
        processed_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"✅ 키워드 '{keyword}' 관련 기사 {len(processed_articles)}개 검색 완료")
        return processed_articles[:15]
        
    except Exception as e:
        logger.error(f"❌ 키워드 '{keyword}' 검색 오류: {e}", exc_info=True)
        return []

@retry_on_exception(max_retries=3, delay=0.5, backoff=2, allowed_exceptions=(requests.RequestException,))
async def search_global_keyword_articles(keyword: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """특정 키워드로 DeepSearch Global API에서 해외 관련 기사들을 검색합니다"""
    if not DEEPSEARCH_API_KEY:
        logger.error("❌ DeepSearch API 키가 설정되지 않음")
        return []
    
    try:
        base_url = DEEPSEARCH_GLOBAL_KEYWORD_URL
        params = {
            "api_key": DEEPSEARCH_API_KEY,
            "keyword": keyword,
            "date_from": start_date,
            "date_to": end_date,
            "page_size": 50
        }
        
        logger.info(f"🌍 해외 키워드 '{keyword}' 기사 검색 중... URL: {base_url}")
        logger.info(f"🌍 파라미터: {params}")
        response = requests.get(base_url, params=params, timeout=15)
        logger.info(f"🌍 응답 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ 해외 키워드 검색 API 호출 실패: {response.status_code}")
            logger.error(f"❌ 응답 내용: {response.text}")
            return []
            
        response.raise_for_status()
        data = response.json()
        
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
        
        processed_articles = []
        for article in articles:
            article_id = generate_article_id(article)
            
            published_at = article.get("published_at", "")
            formatted_date = "날짜 정보 없음"
            if published_at:
                try:
                    if "T" in published_at:
                        formatted_date = published_at.split("T")[0]
                    else:
                        formatted_date = published_at[:10]
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
            
            articles_cache[article_id] = processed_article
            processed_articles.append(processed_article)
        
        processed_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"✅ 해외 키워드 '{keyword}' 관련 기사 {len(processed_articles)}개 검색 완료")
        return processed_articles[:15]
        
    except Exception as e:
        logger.error(f"❌ 해외 키워드 '{keyword}' 검색 오류: {e}", exc_info=True)
        return []

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
                base_url = DEEPSEARCH_KEYWORD_URL
                params = {
                    "api_key": DEEPSEARCH_API_KEY,
                    "keyword": keyword,
                    "date_from": start_date,
                    "date_to": end_date
                }
                response = requests.get(base_url, params=params, timeout=15)
                
                if response.status_code != 200:
                    logger.warning(f"    ❌ '{keyword}' 검색 실패: {response.status_code}")
                    continue
                    
                data = response.json()
                
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
            except Exception as e:
                logger.warning(f"    ❌ '{keyword}' 처리 오류: {e}")
                continue
                
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

def get_original_url_by_id(article_id: str):
    """기사 ID로 원본 URL을 찾습니다"""
    article = articles_cache.get(article_id)
    if article:
        return article.get("url")
    return None

@retry_on_exception(max_retries=3, delay=0.5, backoff=2, allowed_exceptions=(requests.RequestException,))
def deepsearch_api_request(url, params):
    """DeepSearch API 요청 (재시도/로깅 일관성)"""
    logger.info(f"DeepSearch API 요청: {url} | params: {params}")
    response = requests.get(url, params=params, timeout=15)
    logger.info(f"DeepSearch 응답 코드: {response.status_code}")
    response.raise_for_status()
    return response.json() 