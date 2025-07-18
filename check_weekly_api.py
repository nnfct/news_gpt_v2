"""
주차별 API 응답 확인 스크립트
"""
import requests
import json

def check_weekly_data():
    """각 주차별 API 응답 확인"""
    
    weeks = [
        {"week": "1주차", "start": "2025-07-01", "end": "2025-07-05"},
        {"week": "2주차", "start": "2025-07-06", "end": "2025-07-13"},
        {"week": "3주차", "start": "2025-07-14", "end": "2025-07-18"}
    ]
    
    for week_info in weeks:
        print(f"\n📅 {week_info['week']} ({week_info['start']} ~ {week_info['end']})")
        print("=" * 50)
        
        try:
            url = f"http://localhost:8000/weekly-keywords-by-date?start_date={week_info['start']}&end_date={week_info['end']}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 응답 성공")
                print(f"키워드: {data.get('keywords', [])}")
                print(f"주간 정보: {data.get('week_info', 'N/A')}")
                print(f"기사 수: {data.get('article_count', 0)}")
            else:
                print(f"❌ HTTP 오류: {response.status_code}")
                print(f"응답: {response.text}")
                
        except Exception as e:
            print(f"❌ 요청 오류: {e}")

if __name__ == "__main__":
    print("🔍 주차별 API 응답 확인 중...")
    check_weekly_data()
    print("\n✅ 확인 완료!")
