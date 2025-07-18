import os
import time
import requests
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from collections import Counter

load_dotenv()

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

def main():
    """올바른 플로우: DeepSearch → Azure AI Search → GPT-4o → Top 5 키워드"""
    
    print("🚀 올바른 News GPT v2 분석 시작")
    print("=" * 60)
    
    # 1️⃣ DeepSearch API로 IT/기술 뉴스 수집
    print("\n1️⃣ DeepSearch API로 IT/기술 뉴스 수집 중...")
    articles = collect_it_news_from_deepsearch()
    
    if not articles:
        print("❌ 뉴스 수집 실패")
        return
    
    # 2️⃣ Azure AI Search에 업로드
    print(f"\n2️⃣ Azure AI Search에 {len(articles)}개 기사 업로드 중...")
    upload_success = upload_articles_to_azure_search(articles)
    
    if not upload_success:
        print("❌ Azure AI Search 업로드 실패")
        return
    
    # 3️⃣ Azure OpenAI GPT-4o로 키워드 추출
    print(f"\n3️⃣ Azure OpenAI GPT-4o로 키워드 추출 중...")
    keywords = extract_keywords_with_gpt4o(articles)
    
    if not keywords:
        print("❌ 키워드 추출 실패")
        return
    
    # 4️⃣ 키워드 빈도 분석 및 Top 5 선정
    print(f"\n4️⃣ 키워드 빈도 분석 및 Top 5 선정...")
    top_keywords = analyze_keyword_frequency(keywords)
    
    # 5️⃣ 결과 출력
    print("\n" + "=" * 60)
    print("🎯 최종 결과: Top 5 IT/기술 키워드")
    print("=" * 60)
    
    for i, kw in enumerate(top_keywords[:5], 1):
        print(f"{i}. {kw['keyword']} ({kw['count']}회)")
    
    print(f"\n📊 총 수집된 기사: {len(articles)}개")
    print(f"📊 Azure AI Search 업로드: {'성공' if upload_success else '실패'}")
    print(f"📊 추출된 키워드: {len(keywords)}개")
    print("✅ 분석 완료!")

def collect_it_news_from_deepsearch():
    """DeepSearch API로 IT/기술 뉴스 수집"""
    
    if not DEEPSEARCH_API_KEY:
        print("❌ DeepSearch API 키가 설정되지 않음")
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
                    "start_date": "2025-07-14",
                    "end_date": "2025-07-18",
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
                    
                    if "2025-07-14" <= article_date <= "2025-07-18":
                        articles.append({
                            "id": f"news_{len(articles)}_{int(time.time())}",
                            "title": item.get("title", ""),
                            "content": item.get("summary", "") or item.get("content", ""),
                            "date": article_date
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
3. 각 키워드의 예상 빈도도 함께 제공
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
        
        keywords_text = response.choices[0].message.content or ""
        
        # 키워드:빈도 파싱
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

if __name__ == "__main__":
    main()
