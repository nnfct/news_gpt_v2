import os
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import datetime

load_dotenv()

AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")

def upload_test_articles():
    """테스트 기사들을 Azure Search에 업로드"""
    try:
        client = SearchClient(
            endpoint=str(AZURE_SEARCH_ENDPOINT),
            index_name=str(AZURE_SEARCH_INDEX),
            credential=AzureKeyCredential(str(AZURE_SEARCH_API_KEY))
        )
        
        # 테스트 기사 데이터 (URL 제외)
        test_articles = [
            {
                "id": "test_article_1",
                "title": "AI 기술 발전으로 미래 일자리 변화 예상",
                "content": "인공지능 기술의 급속한 발전으로 인해 다양한 산업 분야에서 일자리 구조의 변화가 예상된다고 전문가들이 분석했다. 특히 반복적인 업무는 AI가 대체할 가능성이 높지만, 창의적이고 감정적인 업무는 여전히 인간의 영역으로 남을 것으로 전망된다.",
                "date": "2025-07-18"
            },
            {
                "id": "test_article_2", 
                "title": "반도체 산업 성장과 글로벌 경쟁력 강화",
                "content": "국내 반도체 기업들이 차세대 메모리 반도체 개발에 박차를 가하며 글로벌 시장에서의 경쟁력을 강화하고 있다. 특히 AI 칩과 고성능 메모리 분야에서 혁신적인 기술 개발이 활발히 진행되고 있다.",
                "date": "2025-07-17"
            },
            {
                "id": "test_article_3",
                "title": "클라우드 서비스 시장 확대와 디지털 전환",
                "content": "코로나19 이후 디지털 전환이 가속화되면서 클라우드 컴퓨팅 서비스 시장이 급속히 성장하고 있다. 기업들은 비용 절감과 효율성 향상을 위해 클라우드 기반 인프라로 전환하고 있다.",
                "date": "2025-07-16"
            },
            {
                "id": "test_article_4",
                "title": "메타버스 플랫폼 기술 혁신 동향",
                "content": "메타버스 플랫폼 기술이 빠르게 발전하며 가상현실과 증강현실 기술이 일상생활에 점차 확산되고 있다. 특히 교육, 업무, 엔터테인먼트 분야에서 활용도가 높아지고 있다.",
                "date": "2025-07-15"
            },
            {
                "id": "test_article_5",
                "title": "5G 네트워크 확산과 6G 기술 연구",
                "content": "5G 네트워크가 전국적으로 확산되면서 초고속 통신 서비스가 일반화되고 있다. 동시에 차세대 6G 기술에 대한 연구개발도 본격화되고 있어 통신 기술의 미래가 주목받고 있다.",
                "date": "2025-07-14"
            }
        ]
        
        # 기사 업로드
        result = client.upload_documents(documents=test_articles)
        
        success_count = 0
        for i, res in enumerate(result):
            if res.succeeded:
                success_count += 1
                print(f"✅ 기사 {i+1} 업로드 성공: {test_articles[i]['title']}")
            else:
                print(f"❌ 기사 {i+1} 업로드 실패: {res.error_message}")
        
        print(f"\n📊 총 {len(test_articles)}개 기사 중 {success_count}개 성공적으로 업로드")
        
    except Exception as e:
        print(f"❌ 업로드 오류: {e}")

if __name__ == "__main__":
    print("🔄 테스트 기사 업로드 중...")
    upload_test_articles()
