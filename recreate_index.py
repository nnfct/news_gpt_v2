"""
Azure AI Search 인덱스 재생성 스크립트
기존 인덱스를 삭제하고 새로 생성합니다.
"""

import os
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex, SimpleField, SearchableField, SearchFieldDataType
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

# 환경변수
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")

def recreate_index():
    """인덱스 삭제 및 재생성"""
    
    # 인덱스 클라이언트 생성
    credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)
    client = SearchIndexClient(AZURE_SEARCH_ENDPOINT, credential)
    
    try:
        # 1. 기존 인덱스 삭제
        print(f"🗑️ 기존 인덱스 '{AZURE_SEARCH_INDEX}' 삭제 중...")
        client.delete_index(AZURE_SEARCH_INDEX)
        print("✅ 기존 인덱스 삭제 완료")
        
    except Exception as e:
        print(f"⚠️ 기존 인덱스 삭제 시 오류 (무시 가능): {e}")
    
    try:
        # 2. 새 인덱스 생성
        print(f"🔨 새 인덱스 '{AZURE_SEARCH_INDEX}' 생성 중...")
        
        # 필드 정의
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="title", type=SearchFieldDataType.String, filterable=True, sortable=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SimpleField(name="date", type=SearchFieldDataType.String, filterable=True, sortable=True, facetable=True),
            SimpleField(name="source_url", type=SearchFieldDataType.String),
            SearchableField(name="keyword", type=SearchFieldDataType.String, filterable=True, facetable=True)
        ]
        
        # 인덱스 생성
        index = SearchIndex(name=AZURE_SEARCH_INDEX, fields=fields)
        result = client.create_index(index)
        
        print(f"✅ 새 인덱스 '{result.name}' 생성 완료")
        print("📋 인덱스 필드:")
        for field in result.fields:
            print(f"  - {field.name}: {field.type}")
        
        return True
        
    except Exception as e:
        print(f"❌ 새 인덱스 생성 오류: {e}")
        return False

if __name__ == "__main__":
    recreate_index()
