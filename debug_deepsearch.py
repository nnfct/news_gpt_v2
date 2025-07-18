import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_deepsearch_direct():
    """DeepSearch API 직접 테스트"""
    
    api_key = os.getenv("DEEPSEARCH_API_KEY")
    print(f"API 키: {api_key[:10]}...")
    
    # 원본 DB 키워드 테스트
    print("\n1️⃣ 원본 'DB' 키워드 테스트")
    print("-" * 40)
    
    url = "https://api-v2.deepsearch.com/v1/articles"
    params = {
        "api_key": api_key,
        "q": "DB",
        "limit": 5,
        "start_date": "2025-07-14",
        "end_date": "2025-07-18"
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('data', [])
            print(f"검색된 기사 수: {len(articles)}")
            
            for i, article in enumerate(articles[:3], 1):
                print(f"\n  {i}. 제목: {article.get('title', 'N/A')[:50]}...")
                print(f"     발행일: {article.get('published_at', 'N/A')[:10]}")
                print(f"     URL: {article.get('url', 'N/A')}")
        else:
            print(f"오류: {response.text}")
            
    except Exception as e:
        print(f"예외: {e}")
    
    # 향상된 DB 키워드 테스트
    print("\n2️⃣ 향상된 'DB금융투자' 키워드 테스트")
    print("-" * 40)
    
    params["q"] = "DB금융투자"
    
    try:
        response = requests.get(url, params=params)
        print(f"응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('data', [])
            print(f"검색된 기사 수: {len(articles)}")
            
            for i, article in enumerate(articles[:3], 1):
                print(f"\n  {i}. 제목: {article.get('title', 'N/A')[:50]}...")
                print(f"     발행일: {article.get('published_at', 'N/A')[:10]}")
                print(f"     URL: {article.get('url', 'N/A')}")
        else:
            print(f"오류: {response.text}")
            
    except Exception as e:
        print(f"예외: {e}")

    # OR 조건 검색 테스트
    print("\n3️⃣ OR 조건 검색 테스트")
    print("-" * 40)
    
    params["q"] = '"DB금융투자" OR "DB손해보험" OR "DB그룹"'
    
    try:
        response = requests.get(url, params=params)
        print(f"응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('data', [])
            print(f"검색된 기사 수: {len(articles)}")
            
            for i, article in enumerate(articles[:3], 1):
                print(f"\n  {i}. 제목: {article.get('title', 'N/A')[:50]}...")
                print(f"     발행일: {article.get('published_at', 'N/A')[:10]}")
                print(f"     URL: {article.get('url', 'N/A')}")
        else:
            print(f"오류: {response.text}")
            
    except Exception as e:
        print(f"예외: {e}")

if __name__ == "__main__":
    test_deepsearch_direct()
