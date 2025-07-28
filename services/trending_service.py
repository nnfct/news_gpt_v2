import logging
import time
import feedparser
import urllib.parse
import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dateutil import parser as date_parser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.config import openai_client, AZURE_OPENAI_DEPLOYMENT
from utils.helpers import set_cache

logger = logging.getLogger(__name__)

TRENDING_CACHE_KEY = "google_trending_keywords"

def cache_google_tranding(country_codes):
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
            logger.error(f"Error fetching trends for {geo}: {e}")
            keywords = [f"Sample keyword {i} for {geo}" for i in range(1, 6)]
        finally:
            driver.quit()
        return [{"country": geo, "keyword": kw} for kw in keywords]

    with ThreadPoolExecutor(max_workers=min(len(country_codes), 5)) as executor:
        results = list(executor.map(fetch_keywords, country_codes))

    raw_keywords = [item for sublist in results for item in sublist]
            
    shared_indices = find_shared_keywords_with_llm(raw_keywords)

    for i, item in enumerate(raw_keywords):
        item["shared"] = i in shared_indices

    cache_data = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "data": raw_keywords,
        "status": "success"
    }
    
    set_cache(TRENDING_CACHE_KEY, cache_data)
    logger.info(f"Cached Google Trending Keywords to file: {cache_data}")

def find_shared_keywords_with_llm(raw_keywords):
    """LLM을 사용하여 공유 키워드 찾기"""
    try:
        # 키워드를 LLM이 이해하기 쉬운 형태로 포맷팅
        formatted_keywords = []
        for i, item in enumerate(raw_keywords):
            formatted_keywords.append(f"{i}: '{item['keyword']}' ({item['country']})")
        
        keywords_text = "\n".join(formatted_keywords)

        prompt = f"""
        Here is a list of trending keywords from different countries.
        Your task is to identify **keywords from different countries that refer to the SAME entity**, 
        even if they are written in different languages or slightly different forms.
        
        Keyword list:
        {keywords_text}
        
        Rules:
        - DO NOT group keywords from the same country together.
        - Only group keywords that refer to the EXACT same entity (brand, company, person, product).
        - **If a company name is combined with words like 'stock', 'shares', or '주가' (Korean for stock price), 
        they must be grouped together as the same concept.**
        - Good examples: Tesla/TSLA/테슬라, iPhone/아이폰, Trump/트럼프, 
        **Samsung Electronics/삼성전자/Samsung stock/Samsung Electronics shares**.
        - Do NOT group words that are only thematically related. They must refer to semantically the SAME target.
        
        Respond ONLY in JSON format like this:
        {{"shared_groups": [[0, 5, 12], [3, 8]]}}
        """

        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are an AI assistant that identifies shared trending keywords across multiple countries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )

        response_text = response.choices[0].message.content or "{}"
        
        # LLM 응답에서 JSON 코드 블록 정리 (e.g., ```json ... ```)
        if "```" in response_text:
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]

        try:
            data = json.loads(response_text.strip())
            shared_groups = data.get("shared_groups", [])
            
            # 모든 그룹의 인덱스를 하나의 set으로 통합
            shared_indices = set()
            for group in shared_groups:
                shared_indices.update(group)
                
            return list(shared_indices)
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse JSON from LLM response: '{response_text}', error: {e}")
            return []
    except Exception as e:
        logger.error(f"Error finding shared keywords with LLM: {e}")
        return []

def find_shared_keywords_with_embedding(raw_keywords):
    """임베딩을 사용하여 공유 키워드 찾기"""
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 키워드 그룹핑
        keyword_groups = {}
        for i, item in enumerate(raw_keywords):
            kw = item['keyword']
            if kw not in keyword_groups:
                keyword_groups[kw] = []
            keyword_groups[kw].append(i)

        # 고유 키워드 및 임베딩
        unique_keywords = list(keyword_groups.keys())
        embeddings = model.encode(unique_keywords)
        
        # 코사인 유사도 계산
        cosine_matrix = cosine_similarity(embeddings)
        
        # 유사도 기반 클러스터링
        threshold = 0.8
        clusters = []
        visited = [False] * len(unique_keywords)
        
        for i in range(len(unique_keywords)):
            if not visited[i]:
                cluster = [i]
                visited[i] = True
                for j in range(i + 1, len(unique_keywords)):
                    if not visited[j] and cosine_matrix[i][j] > threshold:
                        cluster.append(j)
                        visited[j] = True
                clusters.append(cluster)

        # 3개국 이상 공유 클러스터 필터링
        shared_indices = set()
        for cluster in clusters:
            countries = set()
            indices_in_cluster = []
            for keyword_index in cluster:
                keyword = unique_keywords[keyword_index]
                for original_index in keyword_groups[keyword]:
                    countries.add(raw_keywords[original_index]['country'])
                    indices_in_cluster.append(original_index)
            
            if len(countries) >= 3:
                shared_indices.update(indices_in_cluster)
                
        return list(shared_indices)
    except Exception as e:
        logger.error(f"Error finding shared keywords with embedding: {e}")
        return []

def get_news(country: str, keyword: str):
    """Google News RSS 피드를 사용하여 특정 국가 및 키워드에 대한 뉴스 가져오기"""
    try:
        encoded_kw = urllib.parse.quote(keyword)
        hl_map = {'US': 'en', 'GB': 'en-GB', 'MX': 'es-419', 'KR': 'ko', 'IN': 'en-IN', 'ZA': 'en-ZA', 'AU': 'en-AU'}
        
        hl = hl_map.get(country, 'en')
        ceid = f"{country}:{hl}"
        url = f"https://news.google.com/rss/search?q={encoded_kw}&hl={hl}&gl={country}&ceid={ceid}"
        
        feed = feedparser.parse(url)
        
        articles = []
        for entry in feed.entries[:5]:  # 상위 5개 기사
            title = entry.title
            link = entry.link
            published_str = getattr(entry, 'published', '')
            published_date = date_parser.parse(entry.published).strftime('%Y-%m-%d')
            
            articles.append({
                "title": title,
                "link": link,
                "published": published_str,
                "published_dt": published_date
            })
            
        return articles
    except Exception as e:
        logger.error(f"Error fetching news for {keyword} in {country}: {e}", exc_info=True)
        return [] 
    
if __name__ == "__main__":
    cache_google_tranding(["US", "GB", "MX", "KR", "IN", "ZA", "AU"])
    