
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 환경변수 로드
load_dotenv()

# Azure OpenAI API 설정
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

# Azure OpenAI 키워드 설명자 API 설정
AZURE_OPENAI_KEYWORD_EXPLAINER_API_KEY = os.getenv("AZURE_OPENAI_KEYWORD_EXPLAINER_API_KEY")
AZURE_OPENAI_KEYWORD_EXPLAINER_ENDPOINT = os.getenv("AZURE_OPENAI_KEYWORD_EXPLAINER_ENDPOINT")
AZURE_OPENAI_KEYWORD_EXPLAINER_DEPLOYMENT = os.getenv("AZURE_OPENAI_KEYWORD_EXPLAINER_DEPLOYMENT")
AZURE_OPENAI_KEYWORD_EXPLAINER_VERSION = os.getenv("AZURE_OPENAI_KEYWORD_EXPLAINER_VERSION")

# DeepSearch API 키
DEEPSEARCH_API_KEY = os.getenv("DEEPSEARCH_API_KEY")

# 이메일 설정
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Azure AI Search (NCS) 설정
AZURE_SEARCH_ENDPOINT_NCS = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY_NCS = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX_NCS = os.getenv("AZURE_SEARCH_INDEX")
AZURE_OPENAI_DEPLOYMENT_NCS = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# Azure OpenAI 클라이언트 초기화
openai_client = None
if all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_ENDPOINT]):
    openai_client = AzureOpenAI(
        api_key=str(AZURE_OPENAI_API_KEY),
        api_version=str(AZURE_OPENAI_API_VERSION),
        azure_endpoint=str(AZURE_OPENAI_ENDPOINT)
    )
    logger.info("✅ Azure OpenAI 클라이언트 초기화 성공")
else:
    logger.warning("⚠️ Azure OpenAI 클라이언트 초기화 실패: 환경 변수를 확인하세요.")

openai_keyword_explainer_client = None
if all([AZURE_OPENAI_KEYWORD_EXPLAINER_API_KEY, AZURE_OPENAI_KEYWORD_EXPLAINER_VERSION, AZURE_OPENAI_KEYWORD_EXPLAINER_ENDPOINT]):
    openai_keyword_explainer_client = AzureOpenAI(
        api_key=str(AZURE_OPENAI_KEYWORD_EXPLAINER_API_KEY),
        api_version=str(AZURE_OPENAI_KEYWORD_EXPLAINER_VERSION),
        azure_endpoint=str(AZURE_OPENAI_KEYWORD_EXPLAINER_ENDPOINT)
    )
    logger.info("✅ Azure OpenAI 키워드 설명자 클라이언트 초기화 성공")
else:
    logger.warning("⚠️ Azure OpenAI 키워드 설명자 클라이언트 초기화 실패: 환경 변수를 확인하세요.")


# Azure AI Search (NCS) 클라이언트 초기화
ncs_search_client: SearchClient | None = None
if all([AZURE_SEARCH_ENDPOINT_NCS, AZURE_SEARCH_KEY_NCS, AZURE_SEARCH_INDEX_NCS]):
    try:
        ncs_search_client = SearchClient(
            endpoint=AZURE_SEARCH_ENDPOINT_NCS,
            index_name=AZURE_SEARCH_INDEX_NCS,
            credential=AzureKeyCredential(AZURE_SEARCH_KEY_NCS)
        )
        logger.info(f"✅ Azure AI Search (NCS) 클라이언트 초기화 성공: {AZURE_SEARCH_INDEX_NCS}")
    except Exception as e:
        logger.error(f"❌ Azure AI Search (NCS) 클라이언트 초기화 실패: {e}", exc_info=True)
else:
    logger.warning("⚠️ Azure AI Search (NCS) 환경 변수가 설정되지 않아 NCS 검색 기능을 사용할 수 없습니다.")

# DeepSearch API URL
DEEPSEARCH_TECH_URL = "https://api-v2.deepsearch.com/v1/articles/tech"
DEEPSEARCH_KEYWORD_URL = "https://api-v2.deepsearch.com/v1/articles"
DEEPSEARCH_GLOBAL_TECH_URL = "https://api-v2.deepsearch.com/v1/global-articles"
DEEPSEARCH_GLOBAL_KEYWORD_URL = "https://api-v2.deepsearch.com/v1/global-articles"

# 캐시 설정
CACHE_EXPIRY_MINUTES = 30
MAX_CACHE_SIZE = 1000

# 구독자 파일
SUBSCRIBERS_FILE = "subscribers.json" 