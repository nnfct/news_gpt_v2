import os
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from error_logger import log_error

load_dotenv()

AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")

try:
    client = SearchClient(
        endpoint=str(AZURE_SEARCH_ENDPOINT),
        index_name=str(AZURE_SEARCH_INDEX),
        credential=AzureKeyCredential(str(AZURE_SEARCH_API_KEY))
    )
    
    # 주간 요약 직접 업로드
    doc = {
        "id": "weekly_summary_2025_week3",
        "title": "2025년 7월 3주차 IT/기술 뉴스 키워드 분석", 
        "content": "2025년 7월 3주차 Top 3 키워드: [AI] [인공지능] [반도체]\n\n상세 통계: AI(18회), 인공지능(12회), 반도체(7회), 기술(5회), 데이터(4회)",
        "date": "2025-07-17"
    }
    
    result = client.upload_documents(documents=[doc])
    if result[0].succeeded:
        print("✅ 주간 요약 업로드 성공!")
        print(f"📄 ID: {doc['id']}")
        print(f"📄 제목: {doc['title']}")
        print(f"📄 내용: {doc['content']}")
    else:
        print(f"❌ 업로드 실패: {result[0].error_message}")
        
except Exception as e:
    log_error(
        error=e,
        file_name="upload_summary.py",
        function_name="main",
        context="주간 요약 업로드 중 오류 발생",
        additional_info={
            "document_id": "weekly_summary_2025_week3",
            "endpoint": AZURE_SEARCH_ENDPOINT,
            "index": AZURE_SEARCH_INDEX
        },
        severity="HIGH"
    )
    print(f"❌ 오류: {e}")
