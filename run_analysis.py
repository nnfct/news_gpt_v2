import os
from dotenv import load_dotenv
import json
import urllib.parse
from collections import Counter
import time

load_dotenv()

import requests
import openai
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import pandas as pd

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def collect_news():
    """네이버 뉴스 API로 IT/기술 분야 7일치 뉴스 수집"""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET or NAVER_CLIENT_ID == "your_naver_client_id":
        print("⚠️ Naver API 키가 설정되지 않아 샘플 데이터를 사용합니다.")
        return [
            {"title": "AI 기술 발전으로 미래 일자리 변화 예상", "content": "인공지능 기술의 급속한 발전으로 인해 다양한 산업 분야에서 일자리 구조의 변화가 예상된다고 전문가들이 분석했다.", "section": "IT/기술", "url": "https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=105&oid=001&aid=0014567890", "date": "2025-07-18"},
            {"title": "반도체 산업 성장과 글로벌 경쟁력", "content": "국내 반도체 기업들이 차세대 메모리 반도체 개발에 박차를 가하며 글로벌 시장에서의 경쟁력을 강화하고 있다.", "section": "IT/기술", "url": "https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=105&oid=001&aid=0014567891", "date": "2025-07-17"},
            {"title": "클라우드 서비스 시장 확대", "content": "코로나19 이후 디지털 전환이 가속화되면서 클라우드 컴퓨팅 서비스 시장이 급속히 성장하고 있다.", "section": "IT/기술", "url": "https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=105&oid=001&aid=0014567892", "date": "2025-07-16"}
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
        
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        
        print(f"🔍 IT/기술 분야 뉴스 수집 중 ({len(tech_keywords)}개 키워드 사용)...")
        
        # 각 키워드별로 뉴스 수집
        for keyword in tech_keywords:
            encoded_query = urllib.parse.quote(keyword)
            # display를 10으로 늘려서 더 많은 뉴스 수집
            url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display=10&start=1&sort=date"
            
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                items = data.get("items", [])
                
                for item in items:
                    # HTML 태그 제거
                    title = item.get("title", "").replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
                    description = item.get("description", "").replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
                    link = item.get("link", "")  # 기사 원문 URL 추가
                    pub_date = item.get("pubDate", "")  # 네이버 API에서 제공하는 발행일
                    
                    # 날짜 형식 변환 (RFC2822 -> YYYY-MM-DD)
                    formatted_date = ""
                    if pub_date:
                        try:
                            from datetime import datetime
                            # 네이버 API pubDate는 "Mon, 17 Jul 2025 14:30:00 +0900" 형식
                            dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
                            formatted_date = dt.strftime("%Y-%m-%d")
                        except:
                            formatted_date = "2025-07-17"  # 기본값
                    else:
                        formatted_date = "2025-07-17"  # 기본값
                    
                    # 중복 제거를 위한 간단한 체크
                    is_duplicate = False
                    for existing_news in news_list:
                        if existing_news["title"] == title:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        news_list.append({
                            "title": title,
                            "content": description,
                            "section": "IT/기술",
                            "keyword": keyword,
                            "date": formatted_date
                        })
                    
                print(f"  ✅ '{keyword}' 키워드로 {len(items)}개 뉴스 수집 (중복 제거 후 추가)")
                
                # API 요청 제한을 피하기 위한 딜레이
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  ❌ '{keyword}' 키워드 검색 오류: {e}")
                time.sleep(1)  # 에러 발생 시 더 긴 딜레이
                continue
        
        print(f"\n✅ 총 {len(news_list)}개 IT/기술 뉴스 수집 완료")
        return news_list
        
    except Exception as e:
        print(f"❌ 네이버 API 오류: {e}")
        print("⚠️ 샘플 데이터를 사용합니다.")
        return [
            {"title": "AI 기술 발전으로 미래 일자리 변화 예상", "content": "인공지능 기술의 급속한 발전으로 인해 다양한 산업 분야에서 일자리 구조의 변화가 예상된다고 전문가들이 분석했다.", "section": "IT/기술", "date": "2025-07-18"},
            {"title": "반도체 산업 성장과 글로벌 경쟁력", "content": "국내 반도체 기업들이 차세대 메모리 반도체 개발에 박차를 가하며 글로벌 시장에서의 경쟁력을 강화하고 있다.", "section": "IT/기술", "date": "2025-07-17"}
        ]

def extract_keywords(news):
    # Azure OpenAI GPT-4o로 키워드 추출 (Top 3만)
    openai.api_type = "azure"
    openai.api_key = AZURE_OPENAI_API_KEY
    openai.azure_endpoint = AZURE_OPENAI_ENDPOINT
    openai.api_version = "2024-02-15-preview"
    prompt = f"다음 뉴스에서 가장 중요한 핵심 키워드 3개만 콤마로 구분해 추출해줘. 순서는 중요도 순으로.\n뉴스: {news['content']}"
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "뉴스에서 가장 중요한 키워드 3개만 추출하는 봇입니다."},
                {"role": "user", "content": prompt}
            ]
        )
        keywords_str = completion.choices[0].message.content
        if not keywords_str:
            return []
        keywords = [k.strip() for k in str(keywords_str).split(",") if k.strip()]
        # Top 3만 반환
        return keywords[:3]
    except Exception as e:
        print(f"키워드 추출 오류: {e}")
        return []

# def generate_cardnews(keywords):
#     # Azure OpenAI GPT-4o로 카드뉴스 생성 (현재 사용하지 않음)
#     openai.api_type = "azure"
#     openai.api_key = AZURE_OPENAI_API_KEY
#     openai.azure_endpoint = AZURE_OPENAI_ENDPOINT
#     openai.api_version = "2024-02-15-preview"
#     prompt = f"다음 키워드로 뉴스 분석 카드뉴스용 요약 텍스트(3~4문장, 300자 내외, 쉽고 명확하게)를 생성해줘.\n키워드: {', '.join(keywords)}"
#     try:
#         completion = openai.chat.completions.create(
#             model="gpt-4o",
#             messages=[
#                 {"role": "system", "content": "카드뉴스용 요약 텍스트를 생성하는 봇입니다."},
#                 {"role": "user", "content": prompt}
#             ]
#         )
#         content = completion.choices[0].message.content
#         if not content:
#             return ""
#         return str(content).strip()
#     except Exception as e:
#         print(f"카드뉴스 생성 오류: {e}")
#         return ""

def get_embedding(text):
    # Azure OpenAI text-embedding-ada-002로 임베딩 생성
    openai.api_type = "azure"
    openai.api_key = AZURE_OPENAI_API_KEY
    openai.azure_endpoint = AZURE_OPENAI_ENDPOINT
    openai.api_version = "2024-02-15-preview"
    try:
        response = openai.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"임베딩 생성 오류: {e}")
        return [0.0] * 1536

def analyze_weekly_keywords(news_list):
    """7일치 뉴스에서 전체 키워드 빈도 분석하여 Top 3 추출"""
    print(f"\n🔍 {len(news_list)}개 뉴스에서 키워드 빈도 분석 중...")
    
    all_keywords = []
    
    # 각 뉴스에서 키워드 추출
    for idx, news in enumerate(news_list):
        print(f"  📄 {idx+1}/{len(news_list)} 처리 중...")
        keywords = extract_keywords(news)
        all_keywords.extend(keywords)
    
    # 키워드 빈도 계산
    keyword_counter = Counter(all_keywords)
    print(f"\n📊 총 {len(all_keywords)}개 키워드 추출, 고유 키워드 {len(keyword_counter)}개")
    
    # Top 3 키워드 선정
    top_3_keywords = [keyword for keyword, count in keyword_counter.most_common(3)]
    
    print(f"\n🏆 1주차 Top 3 키워드:")
    for i, (keyword, count) in enumerate(keyword_counter.most_common(3), 1):
        print(f"  {i}. [{keyword}] - {count}회 언급")
    
    return top_3_keywords, keyword_counter

def upload_news_articles(news_list):
    """뉴스 기사들을 Azure Search에 업로드"""
    try:
        endpoint = AZURE_SEARCH_ENDPOINT or ""
        index_name = AZURE_SEARCH_INDEX or ""
        api_key = AZURE_SEARCH_API_KEY or ""
        client = SearchClient(
            endpoint=str(endpoint),
            index_name=str(index_name),
            credential=AzureKeyCredential(str(api_key))
        )
        
        print(f"📤 {len(news_list)}개 뉴스 기사 업로드 중...")
        
        # 기사 문서 생성
        documents = []
        for i, news in enumerate(news_list):
            doc = {
                "id": f"news_article_{i+1}_{hash(news['title']) % 1000000:06d}",
                "title": news.get("title", ""),
                "content": news.get("content", ""),
                "date": news.get("date", "2025-07-17"),
                "section": news.get("section", "IT/기술"),
                "keyword": news.get("keyword", "")
            }
            documents.append(doc)
        
        # 배치 업로드 (한 번에 최대 1000개)
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            result = client.upload_documents(documents=batch)
            
            success_count = sum(1 for r in result if r.succeeded)
            print(f"  ✅ 배치 {i//batch_size + 1}: {success_count}/{len(batch)}개 성공")
            
        print(f"✅ 총 {len(documents)}개 뉴스 기사 업로드 완료!")
        
    except Exception as e:
        print(f"❌ 뉴스 기사 업로드 오류: {e}")

def upload_weekly_summary(top_3_keywords, keyword_counter):
    """주간 키워드 요약을 Azure Search에 업로드"""
    try:
        endpoint = AZURE_SEARCH_ENDPOINT or ""
        index_name = AZURE_SEARCH_INDEX or ""
        api_key = AZURE_SEARCH_API_KEY or ""
        client = SearchClient(
            endpoint=str(endpoint),
            index_name=str(index_name),
            credential=AzureKeyCredential(str(api_key))
        )
        
        # 주간 요약 문서 생성
        weekly_summary = f"2025년 7월 3주차 Top 3 키워드: [{top_3_keywords[0]}] [{top_3_keywords[1]}] [{top_3_keywords[2]}]"
        
        # 상세 통계 추가
        detailed_stats = []
        for keyword, count in keyword_counter.most_common(10):  # Top 10까지
            detailed_stats.append(f"{keyword}({count}회)")
        
        content = f"{weekly_summary}\n\n상세 통계: " + ", ".join(detailed_stats)
        
        doc = {
            "id": "weekly_summary_2025_week3",  # 주차별 고유 ID
            "title": "2025년 7월 3주차 IT/기술 뉴스 키워드 분석",
            "content": content,
            "date": "2025-07-17"
        }
        
        result = client.upload_documents(documents=[doc])
        if not result[0].succeeded:
            print(f"❌ 주간 요약 업로드 실패: {result[0].error_message}")
        else:
            print(f"✅ 주간 요약 업로드 성공!")
            print(f"📄 업로드된 내용: {content[:100]}...")
            
    except Exception as e:
        print(f"❌ 주간 요약 업로드 오류: {e}")

if __name__ == "__main__":
    print("📰 7일치 뉴스 키워드 분석 스크립트 실행")
    
    # 1단계: 7일치 뉴스 수집
    news_list = collect_news()
    
    # 2단계: 뉴스 기사들을 Azure Search에 업로드
    upload_news_articles(news_list)
    
    # 3단계: 전체 키워드 빈도 분석
    top_3_keywords, keyword_counter = analyze_weekly_keywords(news_list)
    
    # 4단계: 주간 요약 결과 출력
    print(f"\n🎯 최종 결과:")
    print(f"2025년 7월 3주차 Top 3 키워드: [{top_3_keywords[0]}] [{top_3_keywords[1]}] [{top_3_keywords[2]}]")
    
    # 5단계: Azure Search에 주간 요약 업로드
    upload_weekly_summary(top_3_keywords, keyword_counter)
    
    print(f"\n✅ 분석 완료! 웹페이지에서 결과를 확인하세요.")
