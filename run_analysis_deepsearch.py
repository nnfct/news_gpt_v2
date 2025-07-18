import os
import requests
import urllib.parse
import time
from datetime import datetime
from dotenv import load_dotenv
from collections import Counter
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from error_logger import log_error, auto_log_errors

load_dotenv()

# Azure 설정
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")

# DeepSearch API 설정
DEEPSEARCH_API_KEY = os.getenv("DEEPSEARCH_API_KEY")

def collect_news():
    """DeepSearch API로 IT/기술 분야 7일치 뉴스 수집"""
    if not DEEPSEARCH_API_KEY or DEEPSEARCH_API_KEY == "your_deepsearch_api_key_here":
        print("⚠️ DeepSearch API 키가 설정되지 않아 샘플 데이터를 사용합니다.")
        return [
            {"title": "AI 기술 발전으로 미래 일자리 변화 예상", "content": "인공지능 기술의 급속한 발전으로 인해 다양한 산업 분야에서 일자리 구조의 변화가 예상된다고 전문가들이 분석했다.", "section": "IT/기술", "url": "https://news.example.com/ai-jobs", "date": "2025-07-18"},
            {"title": "반도체 산업 성장과 글로벌 경쟁력", "content": "국내 반도체 기업들이 차세대 메모리 반도체 개발에 박차를 가하며 글로벌 시장에서의 경쟁력을 강화하고 있다.", "section": "IT/기술", "url": "https://news.example.com/semiconductor", "date": "2025-07-17"},
            {"title": "클라우드 서비스 시장 확대", "content": "코로나19 이후 디지털 전환이 가속화되면서 클라우드 컴퓨팅 서비스 시장이 급속히 성장하고 있다.", "section": "IT/기술", "url": "https://news.example.com/cloud", "date": "2025-07-16"}
        ]
    
    try:
        news_list = []
        
        # IT/기술 분야 전문 키워드들
        tech_keywords = [
            "인공지능", "AI", "머신러닝", "딥러닝",
            "반도체", "칩", "프로세서", "메모리",
            "클라우드", "데이터센터", "서버",
            "소프트웨어", "앱", "플랫폼",
            "5G", "6G", "통신", "네트워크",
            "블록체인", "암호화폐", "비트코인",
            "메타버스", "VR", "AR", "가상현실",
            "로봇", "자동화", "IoT", "스마트홈"
        ]
        
        print(f"🔍 IT/기술 분야 뉴스 수집 중 ({len(tech_keywords)}개 키워드 사용)...")
        
        # 각 키워드별로 뉴스 수집
        for keyword in tech_keywords:
            try:
                url = "https://api-v2.deepsearch.com/v1/global-articles"
                params = {
                    "api_key": DEEPSEARCH_API_KEY,
                    "q": keyword,
                    "limit": 10,
                    "start_date": "2025-07-12",  # 7일 전
                    "end_date": "2025-07-18",    # 오늘
                    "sort": "published_at:desc"
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                articles = data.get("articles", [])
                
                for article in articles:
                    title = article.get("title", "")
                    content = article.get("summary", "") or article.get("content", "")
                    url = article.get("url", "")
                    pub_date = article.get("published_at", "")
                    
                    # 날짜 형식 변환
                    formatted_date = ""
                    if pub_date:
                        try:
                            if "T" in pub_date:
                                formatted_date = pub_date.split("T")[0]  # YYYY-MM-DD
                            else:
                                formatted_date = pub_date
                        except:
                            formatted_date = "2025-07-18"
                    else:
                        formatted_date = "2025-07-18"
                    
                    # 중복 제거를 위한 간단한 체크
                    is_duplicate = False
                    for existing_news in news_list:
                        if existing_news["title"] == title or existing_news["url"] == url:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate and title and content:
                        news_list.append({
                            "title": title,
                            "content": content,
                            "section": "IT/기술",
                            "url": url,
                            "date": formatted_date
                        })
                
                print(f"  ✅ '{keyword}' 키워드로 {len(articles)}개 뉴스 수집 (중복 제거 후 추가)")
                
                # API 호출 제한을 위한 짧은 지연
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ❌ '{keyword}' 키워드 처리 오류: {e}")
                continue
        
        print(f"\n✅ 총 {len(news_list)}개 IT/기술 뉴스 수집 완료")
        return news_list[:161]  # 최대 161개로 제한
        
    except Exception as e:
        print(f"❌ 뉴스 수집 오류: {e}")
        return []

def extract_keywords(articles):
    """Azure OpenAI GPT-4o를 사용하여 뉴스 기사에서 키워드 추출"""
    
    if not articles:
        print("❌ 분석할 기사가 없습니다.")
        return []
    
    try:
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        
        # 기사 내용 합치기 (처음 50개 기사만 사용)
        articles_text = "\n".join([f"제목: {article['title']}\n내용: {article['content'][:200]}..." 
                                  for article in articles[:50]])
        
        prompt = f"""
다음 IT/기술 뉴스 기사들을 분석하고 가장 중요한 키워드 10개를 추출해주세요.

기사 내용:
{articles_text}

요구사항:
1. IT/기술 분야에서 현재 주목받는 키워드 위주로 선정
2. 단순한 일반 명사가 아닌 구체적이고 의미있는 키워드
3. 한국어로 응답
4. 각 키워드는 띄어쓰기 없이 하나의 단어로 구성
5. 응답 형식: 키워드1, 키워드2, 키워드3, ... (콤마로 구분)

키워드:
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 IT/기술 분야 뉴스 전문 분석가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3
        )
        
        keywords_text = response.choices[0].message.content.strip()
        keywords = [keyword.strip() for keyword in keywords_text.split(',')]
        
        # 키워드 정리 (빈 문자열 제거)
        keywords = [k for k in keywords if k and len(k) > 1]
        
        print(f"✅ GPT-4o로 {len(keywords)}개 키워드 추출 완료")
        print(f"📝 추출된 키워드: {', '.join(keywords)}")
        
        return keywords
        
    except Exception as e:
        print(f"❌ 키워드 추출 오류: {e}")
        # 기본 키워드 반환
        return ["인공지능", "AI", "반도체", "클라우드", "메타버스", "5G", "블록체인", "자동화", "IoT", "빅데이터"]

def upload_to_azure_search(articles, keywords):
    """Azure AI Search에 뉴스 기사 업로드"""
    
    try:
        search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT,
            index_name=AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
        )
        
        # 업로드할 문서 준비
        documents = []
        for i, article in enumerate(articles):
            doc = {
                "id": f"news_{i}_{int(time.time())}",
                "title": article["title"],
                "content": article["content"],
                "date": article["date"],
                "section": article.get("section", "IT/기술"),
                "url": article.get("url", "")
            }
            documents.append(doc)
        
        # 배치 업로드 (50개씩)
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            result = search_client.upload_documents(batch)
            
            success_count = len([r for r in result if r.succeeded])
            print(f"📤 배치 {i//batch_size + 1}: {success_count}/{len(batch)}개 업로드 성공")
        
        print(f"✅ 총 {len(documents)}개 문서 Azure AI Search 업로드 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ Azure AI Search 업로드 오류: {e}")
        return False

def generate_analysis_report(articles, keywords):
    """분석 보고서 생성"""
    
    try:
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        
        keywords_text = ", ".join(keywords[:10])
        
        prompt = f"""
다음 IT/기술 뉴스 데이터를 바탕으로 주간 트렌드 분석 보고서를 작성해주세요.

수집된 뉴스: {len(articles)}개
주요 키워드: {keywords_text}

다음 형식으로 보고서를 작성해주세요:

## 🔍 주간 IT/기술 트렌드 분석 보고서

### 📊 수집 현황
- 총 기사 수: {len(articles)}개
- 수집 기간: 2025-07-12 ~ 2025-07-18
- 주요 섹션: IT/기술

### 🎯 핵심 키워드
[상위 10개 키워드에 대한 간단한 설명]

### 📈 주요 트렌드
[현재 IT/기술 분야에서 주목받는 3가지 트렌드]

### 💡 향후 전망
[향후 1-2주간 예상되는 기술 트렌드]

한국어로 작성하고, 전문적이면서도 이해하기 쉽게 작성해주세요.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 IT/기술 분야 전문 애널리스트입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        report = response.choices[0].message.content.strip()
        
        # 보고서 파일로 저장
        with open("weekly_analysis_report.md", "w", encoding="utf-8") as f:
            f.write(report)
            
        print("✅ 주간 분석 보고서 생성 완료 (weekly_analysis_report.md)")
        print("=" * 50)
        print(report)
        
        return report
        
    except Exception as e:
        print(f"❌ 분석 보고서 생성 오류: {e}")
        return None

def main():
    """메인 분석 실행"""
    print("🚀 DeepSearch API 기반 뉴스 분석 시작...")
    print("=" * 50)
    
    # 1. 뉴스 수집
    print("\n1️⃣ 뉴스 수집 단계")
    articles = collect_news()
    
    if not articles:
        print("❌ 뉴스 수집 실패")
        return
    
    # 2. 키워드 추출
    print("\n2️⃣ 키워드 추출 단계")
    keywords = extract_keywords(articles)
    
    # 3. Azure AI Search 업로드
    print("\n3️⃣ Azure AI Search 업로드 단계")
    upload_success = upload_to_azure_search(articles, keywords)
    
    # 4. 분석 보고서 생성
    print("\n4️⃣ 분석 보고서 생성 단계")
    report = generate_analysis_report(articles, keywords)
    
    # 5. 결과 요약
    print("\n" + "=" * 50)
    print("🎉 분석 완료!")
    print(f"📰 수집된 뉴스: {len(articles)}개")
    print(f"🔍 추출된 키워드: {len(keywords)}개")
    print(f"☁️ Azure 업로드: {'성공' if upload_success else '실패'}")
    print(f"📊 분석 보고서: {'생성 완료' if report else '생성 실패'}")
    
    if keywords:
        print(f"\n🎯 주요 키워드: {', '.join(keywords[:5])}")

if __name__ == "__main__":
    main()
