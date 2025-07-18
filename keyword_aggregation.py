import os
import requests
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

DEEPSEARCH_API_KEY = os.getenv("DEEPSEARCH_API_KEY")

def get_weekly_hot_keywords_from_aggregation(start_date, end_date, top_n=5):
    """DeepSearch API aggregation을 사용해서 실제 주간 핫 키워드 추출"""
    
    hot_keywords = []
    
    # 1. 주요 기업별 언급 빈도 (Top 5)
    companies_data = get_aggregation_data(
        groupby="companies.name",
        date_from=start_date,
        date_to=end_date,
        page_size=top_n
    )
    
    if companies_data:
        print(f"📊 {start_date} ~ {end_date} 기업별 언급 빈도 Top {top_n}:")
        for i, item in enumerate(companies_data[:top_n], 1):
            company = item['key']
            count = item['doc_count']
            hot_keywords.append(company)
            print(f"  {i}. {company}: {count:,}개")
    
    # 2. 전기차 관련 기업 (Top 3)
    ev_companies = get_aggregation_data(
        keyword="전기차",
        groupby="companies.name", 
        date_from=start_date,
        date_to=end_date,
        page_size=3
    )
    
    if ev_companies:
        print(f"\n🚗 전기차 관련 기업 Top 3:")
        for i, item in enumerate(ev_companies[:3], 1):
            company = item['key']
            count = item['doc_count']
            if company not in hot_keywords:
                hot_keywords.append(f"전기차_{company}")
            print(f"  {i}. {company}: {count:,}개")
    
    # 3. AI 관련 기업 (Top 3)
    ai_companies = get_aggregation_data(
        keyword="인공지능",
        groupby="companies.name",
        date_from=start_date,
        date_to=end_date,
        page_size=3
    )
    
    if ai_companies:
        print(f"\n🤖 AI 관련 기업 Top 3:")
        for i, item in enumerate(ai_companies[:3], 1):
            company = item['key']
            count = item['doc_count']
            if company not in hot_keywords:
                hot_keywords.append(f"AI_{company}")
            print(f"  {i}. {company}: {count:,}개")
    
    # 4. 섹션별 분포
    sections_data = get_aggregation_data(
        groupby="sections",
        date_from=start_date,
        date_to=end_date,
        page_size=5
    )
    
    if sections_data:
        print(f"\n📰 섹션별 기사 수 Top 5:")
        section_names = {
            'society': '사회',
            'economy': '경제', 
            'entertainment': '연예',
            'world': '국제',
            'politics': '정치',
            'sports': '스포츠',
            'culture': '문화',
            'tech': '기술',
            'science': '과학'
        }
        for i, item in enumerate(sections_data[:5], 1):
            section = item['key']
            count = item['doc_count']
            section_kr = section_names.get(section, section)
            print(f"  {i}. {section_kr}: {count:,}개")
    
    return hot_keywords[:10]  # 최대 10개 키워드 반환

def get_aggregation_data(groupby, date_from=None, date_to=None, keyword=None, page_size=10):
    """DeepSearch API aggregation 호출"""
    
    if not DEEPSEARCH_API_KEY:
        print("❌ DeepSearch API 키가 설정되지 않았습니다.")
        return None
    
    url = "https://api-v2.deepsearch.com/v1/articles/aggregation"
    params = {
        "groupby": groupby,
        "page_size": page_size,
        "api_key": DEEPSEARCH_API_KEY
    }
    
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to
    if keyword:
        params["keyword"] = keyword
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get('data', [])
        
    except Exception as e:
        print(f"❌ Aggregation API 호출 오류: {e}")
        return None

def test_weekly_keywords():
    """주간별 핫 키워드 테스트"""
    
    print("🔥 주간별 핫 키워드 분석")
    print("=" * 80)
    
    weeks = [
        {"name": "1주차", "start": "2025-07-01", "end": "2025-07-05"},
        {"name": "2주차", "start": "2025-07-06", "end": "2025-07-13"},
        {"name": "3주차", "start": "2025-07-14", "end": "2025-07-18"}
    ]
    
    for week in weeks:
        print(f"\n🗓️ {week['name']} ({week['start']} ~ {week['end']})")
        print("-" * 60)
        
        keywords = get_weekly_hot_keywords_from_aggregation(
            week['start'], 
            week['end']
        )
        
        print(f"\n✨ 추출된 핫 키워드: {keywords}")
        print("=" * 80)

if __name__ == "__main__":
    test_weekly_keywords()
