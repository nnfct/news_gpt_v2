# 🚨 Error History - News GPT v2

## 에러 이력 관리 시스템

이 파일은 News GPT v2 프로젝트에서 발생한 모든 에러를 기록하고 추적하기 위한 파일입니다.

### 📋 에러 기록 형식

```
## 🔴 [날짜] [시간] - [에러 타입]
- **파일**: 에러 발생 파일
- **함수**: 에러 발생 함수
- **에러 메시지**: 구체적인 에러 내용
- **상황**: 에러 발생 상황 설명
- **해결방안**: 해결 방법 (해결된 경우)
- **상태**: 🔴 미해결 / 🟡 진행중 / 🟢 해결완료
```

---

## 📊 에러 통계

- **총 에러 수**: 4개
- **해결된 에러**: 1개
- **미해결 에러**: 3개
- **마지막 업데이트**: 2025-07-18 11:16:42

---

## 🔍 에러 이력

### 2025-07-18 (목요일)

<!-- 에러 기록이 여기에 자동으로 추가됩니다 -->

---

## 🛠️ 자주 발생하는 에러 패턴


## 🟢 [2025-07-18] [11:09:17] - ValueError
- **파일**: test.py
- **함수**: test_function
- **심각도**: LOW
- **에러 메시지**: `테스트 에러입니다`
- **상황**: 에러 로깅 시스템 테스트
- **스택 트레이스**: 
```
Traceback (most recent call last):
  File "C:\Users\USER\Documents\GitHub\news_gpt_v2\error_logger.py", line 265, in <module>
    raise ValueError("테스트 에러입니다")
ValueError: 테스트 에러입니다

```
- **추가 정보**: 
```json
{
  "test": true
}
```
- **해결방안**: 미해결
- **상태**: 🔴 미해결

---


## 🔴 [2025-07-18] [11:15:29] - HttpResponseError
- **파일**: main.py
- **함수**: analyze_keyword_dynamically
- **심각도**: HIGH
- **에러 메시지**: `() Invalid expression: Could not find a property named 'section' on type 'search.document'.

Parameter name: $select
Code: 
Message: Invalid expression: Could not find a property named 'section' on type 'search.document'.

Parameter name: $select`
- **상황**: 키워드 분석 중 오류 발생 - 키워드: 테스트
- **스택 트레이스**: 
```
Traceback (most recent call last):
  File "C:\Users\USER\Documents\GitHub\news_gpt_v2\main.py", line 898, in analyze_keyword_dynamically
    for doc in search_results:
  File "C:\Users\USER\Documents\GitHub\news_gpt_v2\.venv\Lib\site-packages\azure\search\documents\_paging.py", line 54, in __next__
    return next(self._page_iterator)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\USER\Documents\GitHub\news_gpt_v2\.venv\Lib\site-packages\azure\core\paging.py", line 82, in __next__
    self._response = self._get_next(self.continuation_token)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\USER\Documents\GitHub\news_gpt_v2\.venv\Lib\site-packages\azure\search\documents\_paging.py", line 125, in _get_next_cb
    return self._client.documents.search_post(search_request=self._initial_query.request, **self._kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\USER\Documents\GitHub\news_gpt_v2\.venv\Lib\site-packages\azure\core\tracing\decorator.py", line 119, in wrapper_use_tracer
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\USER\Documents\GitHub\news_gpt_v2\.venv\Lib\site-packages\azure\search\documents\_generated\operations\_documents_operations.py", line 754, in search_post
    raise HttpResponseError(response=response, model=error)
azure.core.exceptions.HttpResponseError: () Invalid expression: Could not find a property named 'section' on type 'search.document'.

Parameter name: $select
Code: 
Message: Invalid expression: Could not find a property named 'section' on type 'search.document'.

Parameter name: $select

```
- **추가 정보**: 
```json
{
  "keyword": "테스트",
  "search_attempted": true
}
```
- **해결방안**: 미해결
- **상태**: 🔴 미해결

---


## 🔴 [2025-07-18] [11:16:42] - HttpResponseError
- **파일**: main.py
- **함수**: analyze_keyword_dynamically
- **심각도**: HIGH
- **에러 메시지**: `() Invalid expression: Could not find a property named 'keyword' on type 'search.document'.

Parameter name: $select
Code: 
Message: Invalid expression: Could not find a property named 'keyword' on type 'search.document'.

Parameter name: $select`
- **상황**: 키워드 분석 중 오류 발생 - 키워드: 인공지능
- **스택 트레이스**: 
```
Traceback (most recent call last):
  File "C:\Users\USER\Documents\GitHub\news_gpt_v2\main.py", line 898, in analyze_keyword_dynamically
    for doc in search_results:
  File "C:\Users\USER\Documents\GitHub\news_gpt_v2\.venv\Lib\site-packages\azure\search\documents\_paging.py", line 54, in __next__
    return next(self._page_iterator)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\USER\Documents\GitHub\news_gpt_v2\.venv\Lib\site-packages\azure\core\paging.py", line 82, in __next__
    self._response = self._get_next(self.continuation_token)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\USER\Documents\GitHub\news_gpt_v2\.venv\Lib\site-packages\azure\search\documents\_paging.py", line 125, in _get_next_cb
    return self._client.documents.search_post(search_request=self._initial_query.request, **self._kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\USER\Documents\GitHub\news_gpt_v2\.venv\Lib\site-packages\azure\core\tracing\decorator.py", line 119, in wrapper_use_tracer
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\USER\Documents\GitHub\news_gpt_v2\.venv\Lib\site-packages\azure\search\documents\_generated\operations\_documents_operations.py", line 754, in search_post
    raise HttpResponseError(response=response, model=error)
azure.core.exceptions.HttpResponseError: () Invalid expression: Could not find a property named 'keyword' on type 'search.document'.

Parameter name: $select
Code: 
Message: Invalid expression: Could not find a property named 'keyword' on type 'search.document'.

Parameter name: $select

```
- **추가 정보**: 
```json
{
  "keyword": "인공지능",
  "search_attempted": true
}
```
- **해결방안**: 미해결
- **상태**: 🔴 미해결

---

### 1. Azure API 관련 에러
- **원인**: API 키 만료, 요청 제한 초과
- **해결방안**: 환경변수 확인, 요청 간격 조정

### 2. 네이버 API 관련 에러
- **원인**: Too Many Requests (429 에러)
- **해결방안**: 요청 간격 늘리기, 재시도 로직 추가

### 3. 데이터베이스 관련 에러
- **원인**: 스키마 불일치, 인덱스 없음
- **해결방안**: 스키마 검증, 인덱스 생성 확인

### 4. 인코딩 관련 에러
- **원인**: 한글 문자 처리 오류
- **해결방안**: UTF-8 명시적 설정

---

## 📈 에러 예방 가이드

1. **API 호출 전 환경변수 검증**
2. **요청 간격 및 재시도 로직 구현**
3. **데이터 유효성 검증**
4. **예외 처리 로직 강화**
5. **로그 레벨 설정 및 모니터링**
