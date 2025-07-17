import os
from dotenv import load_dotenv
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")

try:
    # 인덱스 관리 클라이언트로 인덱스 목록 조회
    index_client = SearchIndexClient(
        endpoint=str(AZURE_SEARCH_ENDPOINT),
        credential=AzureKeyCredential(str(AZURE_SEARCH_API_KEY))
    )
    
    indexes = index_client.list_indexes()
    print("📋 사용 가능한 인덱스 목록:")
    
    for index in indexes:
        print(f"  - {index.name}")
        
except Exception as e:
    print(f"❌ 인덱스 목록 조회 오류: {e}")
