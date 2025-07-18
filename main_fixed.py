import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from collections import Counter
import requests
import time
from datetime import datetime, timedelta
import uvicorn

load_dotenv()

app = FastAPI()

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
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
DEEPSEARCH_API_KEY = os.getenv("DEEPSEARCH_API_KEY")

# Azure OpenAI 클라이언트 초기화
openai_client = AzureOpenAI(
    api_key=str(AZURE_OPENAI_API_KEY),
    api_version="2024-02-15-preview",
    azure_endpoint=str(AZURE_OPENAI_ENDPOINT)
)

@app.get("/")
async def serve_home():
    """메인 페이지 제공"""
    return FileResponse("index.html")

@app.get("/api/keywords")
async def get_weekly_keywords():
    """올바른 플로우: DeepSearch → Azure AI Search → GPT-4o → Top 5 키워드 (기업명 제외)"""
    
    try:
        print("🚀 올바른 News GPT v2 분석 시작")
        
        # 1️⃣ DeepSearch API로 IT/기술 뉴스 수집
        print("1️⃣ DeepSearch API로 IT/기술 뉴스 수집 중...")
        articles = await collect_it_news_from_deepsearch()
        
        if not articles:
            return {"error": "뉴스 수집 실패", "keywords": []}
        
        # 2️⃣ Azure AI Search에 업로드
        print(f"2️⃣ Azure AI Search에 {len(articles)}개 기사 업로드 중...")
        upload_success = await upload_articles_to_azure_search(articles)
        
        if not upload_success:
            return {"error": "Azure AI Search 업로드 실패", "keywords": []}
        
        # 3️⃣ Azure OpenAI GPT-4o로 키워드 추출 (기업명 제외)
        print("3️⃣ Azure OpenAI GPT-4o로 키워드 추출 중...")
        keywords = await extract_keywords_with_gpt4o(articles)
        
        if not keywords:
            return {"error": "키워드 추출 실패", "keywords": []}
        
        # 4️⃣ 키워드 빈도 분석 및 Top 5 선정
        print("4️⃣ 키워드 빈도 분석 및 Top 5 선정...")
        top_keywords = analyze_keyword_frequency(keywords)
        
        # Top 5 키워드 반환
        result = []
        for i, kw in enumerate(top_keywords[:5], 1):
            result.append({
                "rank": i,
                "keyword": kw['keyword'],
                "count": kw['count'],
                "source": "IT기술"
            })
        
        return {
            "keywords": result,
            "total_articles": len(articles),
            "analysis_complete": True,
            "flow": "DeepSearch → Azure AI Search → GPT-4o → Top 5"
        }
        
    except Exception as e:
        print(f"❌ 키워드 분석 오류: {e}")
        return {"error": str(e), "keywords": []}

async def collect_it_news_from_deepsearch():
    """DeepSearch API로 IT/기술 뉴스 수집"""
    
    if not DEEPSEARCH_API_KEY:
        print("❌ DeepSearch API 키가 설정되지 않음")
        return []
    
    try:
        articles = []
        tech_keywords = [
            "인공지능", "AI", "머신러닝", "딥러닝", "반도체", "칩", "프로세서", 
            "클라우드", "데이터센터", "소프트웨어", "5G", "6G", "블록체인", 
            "메타버스", "VR", "AR", "로봇", "자동화", "IoT", "빅데이터",
            "차세대", "혁신기술", "디지털전환", "스마트팩토리", "양자컴퓨터"
        ]
        
        print(f"🔍 IT/기술 키워드 {len(tech_keywords)}개로 뉴스 수집 중...")
        
        # 날짜 범위를 더 넓게 (최근 7일)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        for keyword in tech_keywords:
            try:
                url = "https://api-v2.deepsearch.com/v1/articles"
                params = {
                    "api_key": DEEPSEARCH_API_KEY,
                    "q": keyword,
                    "limit": 20,  # 더 많은 기사 수집
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
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
                    
                    articles.append({
                        "id": f"news_{len(articles)}_{int(time.time())}",
                        "title": item.get("title", ""),
                        "content": item.get("summary", "") or item.get("content", ""),
                        "date": article_date
                    })
                
                print(f"  ✅ '{keyword}': {len(data.get('data', []))}개 기사 수집")
                time.sleep(0.05)  # API 제한 방지
                
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

async def upload_articles_to_azure_search(articles):
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

async def extract_keywords_with_gpt4o(articles):
    """Azure OpenAI GPT-4o로 키워드 추출 (기업명 제외)"""
    
    try:
        # 기사 내용 합치기 (최대 100개 기사)
        articles_text = "\n".join([
            f"제목: {article['title']}\n내용: {article['content'][:300]}..."
            for article in articles[:100]
        ])
        
        prompt = f"""
다음 IT/기술 뉴스 기사들을 분석하고 가장 중요한 **기술 키워드**만 추출해주세요.

기사 내용:
{articles_text}

⚠️ 중요한 요구사항:
1. **기업명/회사명은 절대 포함하지 마세요** (삼성, 애플, 구글, 네이버, 카카오, SK, LG, 현대 등 모든 기업명 제외)
2. **기술 분야 키워드만 추출하세요** (예: 인공지능, 반도체, 클라우드, 5G, 블록체인 등)
3. 구체적이고 의미있는 기술 용어 위주로 선정
4. 각 키워드의 예상 빈도도 함께 제공 (1-50 범위)
5. 한국어로 응답
6. **응답 형식**: 키워드1:빈도1, 키워드2:빈도2, ... (콤마로 구분)

기술 키워드:
"""
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 IT/기술 뉴스 전문 키워드 분석가입니다. 기업명은 절대 포함하지 않고 기술 용어만 추출합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.2
        )
        
        keywords_text = response.choices[0].message.content or ""
        print(f"GPT-4o 응답: {keywords_text}")
        
        # 키워드:빈도 파싱
        keywords = []
        for item in keywords_text.split(','):
            if ':' in item:
                parts = item.strip().split(':', 1)
                keyword = parts[0].strip()
                try:
                    count = int(parts[1].strip())
                    # 기업명 필터링 (추가 보안)
                    company_names = ['삼성', '애플', '구글', '네이버', '카카오', 'SK', 'LG', '현대', 
                                   'TSMC', '엔비디아', '인텔', '퀄컴', 'AMD', 'Microsoft', 'IBM']
                    if not any(company in keyword for company in company_names):
                        keywords.append({"keyword": keyword, "count": count})
                except:
                    if not any(company in keyword for company in company_names):
                        keywords.append({"keyword": keyword, "count": 15})
        
        print(f"✅ GPT-4o로 {len(keywords)}개 기술 키워드 추출 완료")
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
    
    return sorted_keywords

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010, reload=True)
