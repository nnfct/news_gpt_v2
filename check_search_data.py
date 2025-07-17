import os
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")

def check_search_data():
    """Azure Search에 저장된 데이터 확인"""
    try:
        client = SearchClient(
            endpoint=str(AZURE_SEARCH_ENDPOINT),
            index_name=str(AZURE_SEARCH_INDEX),
            credential=AzureKeyCredential(str(AZURE_SEARCH_API_KEY))
        )
        
        # 모든 문서 조회
        results = client.search(search_text="*", top=20)
        
        print("🔍 Azure Search 저장 데이터 확인:")
        print("-" * 50)
        
        for i, doc in enumerate(results, 1):
            print(f"📄 문서 {i}:")
            print(f"  ID: {doc.get('id', 'N/A')}")
            print(f"  제목: {doc.get('title', 'N/A')}")
            print(f"  날짜: {doc.get('date', 'N/A')}")
            print(f"  URL: {doc.get('url', 'N/A')}")
            print(f"  내용: {doc.get('content', 'N/A')[:100]}...")
            print()
            
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    check_search_data()
