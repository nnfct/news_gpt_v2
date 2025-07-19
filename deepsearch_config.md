# DeepSearch API URL 설정 가이드

## 🔧 필요한 URL 설정

새로운 워크플로우를 위해 다음 2개의 DeepSearch API URL을 정확히 설정해야 합니다:

### 1. Tech 기사 수집용 URL
```python
DEEPSEARCH_TECH_URL = "https://api-v2.deepsearch.com/v1/articles/tech"
```
- **용도**: 1단계에서 Tech 카테고리 기사들을 수집
- **파라미터**: 
  - `api_key`: DeepSearch API 키
  - `date_from`: 시작 날짜 (YYYY-MM-DD)
  - `date_to`: 종료 날짜 (YYYY-MM-DD)
  - `page_size`: 결과 개수 (기본 100)

### 2. 키워드 기사 검색용 URL  
```python
DEEPSEARCH_KEYWORD_URL = "https://api-v2.deepsearch.com/v1/articles/search"
```
- **용도**: 4단계에서 추출된 키워드로 관련 기사 검색
- **파라미터**:
  - `api_key`: DeepSearch API 키  
  - `q`: 검색 키워드
  - `date_from`: 시작 날짜 (YYYY-MM-DD)
  - `date_to`: 종료 날짜 (YYYY-MM-DD)
  - `page_size`: 결과 개수 (기본 20)

## 🚨 URL 확인 필요사항

현재 main.py에 임시 URL이 설정되어 있습니다:
```python
# main.py 47-48줄
DEEPSEARCH_TECH_URL = "https://api-v2.deepsearch.com/v1/articles/tech"  # Tech 기사 검색용
DEEPSEARCH_KEYWORD_URL = "https://api-v2.deepsearch.com/v1/articles/search"  # 키워드 기사 검색용
```

**사용자가 제공해야 할 정보:**
1. ✅ Tech 카테고리 기사 수집을 위한 정확한 URL과 파라미터 구조
2. ✅ 키워드 검색을 위한 정확한 URL과 파라미터 구조

## 📝 현재 워크플로우

```
1️⃣ /api/keywords?start_date=2025-07-14&end_date=2025-07-18
   ↓ fetch_tech_articles() 
   └── DEEPSEARCH_TECH_URL 호출

2️⃣ extract_keywords_with_gpt()
   ↓ GPT-4o로 키워드 추출
   └── store_keywords_in_memory()

3️⃣ /api/keyword-articles/{keyword}?start_date=2025-07-14&end_date=2025-07-18
   ↓ search_articles_by_keyword()
   └── DEEPSEARCH_KEYWORD_URL 호출

4️⃣ /api/redirect/{article_id}
   ↓ get_original_url_by_id()
   └── 원본 URL로 리다이렉트
```

## 🔄 URL 업데이트 방법

정확한 URL을 받으면 main.py의 47-48줄을 수정:

```python
# 올바른 URL로 교체
DEEPSEARCH_TECH_URL = "정확한_tech_url_여기에"
DEEPSEARCH_KEYWORD_URL = "정확한_keyword_search_url_여기에"
```

## 🧪 테스트 예시

URL 설정 후 다음과 같이 테스트 가능:

```bash
# 1. 키워드 추출 테스트
curl "http://localhost:8000/api/keywords?start_date=2025-07-14&end_date=2025-07-18"

# 2. 키워드 기사 검색 테스트  
curl "http://localhost:8000/api/keyword-articles/인공지능?start_date=2025-07-14&end_date=2025-07-18"

# 3. 리다이렉트 테스트
curl "http://localhost:8000/api/redirect/article_id_123"
```
