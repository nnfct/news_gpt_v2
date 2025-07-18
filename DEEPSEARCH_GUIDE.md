# 🚀 DeepSearch API 실사용 가이드

## 📋 완료된 변경사항

✅ **코드 업데이트 완료:**
- `main.py`: Naver API → DeepSearch API 변경
- `README.md`: 문서 업데이트
- `requirements.md`: 요구사항 업데이트
- `design.md`: 설계 문서 업데이트
- `run_analysis_deepsearch.py`: 새로운 분석 스크립트 생성

✅ **환경 변수 설정:**
- `.env` 파일에 `DEEPSEARCH_API_KEY` 추가됨
- 기존 Naver API 키 제거

## 🎯 실사용 단계별 가이드

### 1단계: 환경 설정

```bash
# 1. 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 2. 필요한 패키지 설치
pip install -r requirements.txt

# 3. 추가 패키지 설치 (누락된 경우)
pip install azure-search-documents azure-core openai python-dotenv
```

### 2단계: 환경 변수 확인

`.env` 파일에 다음 내용이 설정되어 있는지 확인:

```env
# Azure OpenAI 설정
AZURE_OPENAI_API_KEY=F6DWDThuZsAQHAGDB8zwXNgsQGZC12H5NMK8oSR4HgP6RIvxkiijJQQJ99BGACYeBjFXJ3w3AAABACOGc3Go
AZURE_OPENAI_ENDPOINT=https://7ai-2nd-team02.openai.azure.com/

# Azure AI Search 설정
AZURE_SEARCH_API_KEY=94qt8bkIoISAJjRoYN3FNcPqCZGhSfXEOfjUi1f5SOAzSeDNDgyy
AZURE_SEARCH_ENDPOINT=https://7ai-2nd-team02.search.windows.net
AZURE_SEARCH_INDEX=news_index

# DeepSearch 뉴스 API 설정
DEEPSEARCH_API_KEY=5e0b0dba14d846918383174f356dd683
```

### 3단계: 서버 시작

```bash
# 방법 1: 직접 시작
python main.py

# 방법 2: uvicorn 사용
uvicorn main:app --reload --port 8000

# 방법 3: 배치 파일 사용
start_server.bat
```

### 4단계: 웹 인터페이스 접속

브라우저에서 다음 주소로 접속:
- http://localhost:8000

### 5단계: 뉴스 분석 테스트

새로운 DeepSearch API 기반 분석 실행:

```bash
# 새로운 분석 스크립트 실행
python run_analysis_deepsearch.py
```

## 🔧 주요 변경사항

### API 엔드포인트 변경
- **이전**: `https://openapi.naver.com/v1/search/news.json`
- **현재**: `https://api-v2.deepsearch.com/v1/global-articles`

### 인증 방식 변경
- **이전**: `X-Naver-Client-Id`, `X-Naver-Client-Secret` 헤더
- **현재**: `api_key` 쿼리 파라미터

### 응답 구조 변경
- **이전**: `{"items": [...]}`
- **현재**: `{"articles": [...]}`

### 날짜 형식 변경
- **이전**: RFC 2822 형식 (`"Mon, 18 Jul 2025 14:30:00 +0900"`)
- **현재**: ISO 8601 형식 (`"2025-07-18T14:30:00Z"`)

## 🚨 현재 알려진 이슈

1. **DeepSearch API 데이터 부족**
   - 현재 API에서 검색 결과가 0개 반환
   - 실제 데이터가 있는지 확인 필요

2. **환경 문제**
   - 일부 환경에서 azure-search 모듈 인식 실패
   - 가상환경 재설치 필요할 수 있음

## 🎯 추천 실사용 순서

1. **환경 설정 완료**: 가상환경 + 패키지 설치
2. **API 키 확인**: DeepSearch API 키 작동 여부 확인
3. **서버 시작**: 로컬에서 서버 구동 확인
4. **웹 인터페이스 테스트**: 브라우저에서 접속 확인
5. **API 응답 확인**: 키워드 클릭 시 DeepSearch API 호출 확인

## 📊 Git 브랜치 관리

현재 `deepsearch-api-test` 브랜치에서 작업 중:

```bash
# 현재 상태 확인
git status

# 변경사항 푸시
git push origin deepsearch-api-test

# 메인 브랜치로 병합 (준비되면)
git checkout main
git merge deepsearch-api-test
```

## 🔄 롤백 방법

문제가 발생하면 언제든지 이전 Naver API 버전으로 롤백 가능:

```bash
# 메인 브랜치로 돌아가기
git checkout main

# 또는 특정 커밋으로 롤백
git reset --hard <commit-hash>
```

## 💡 다음 단계 개선사항

1. **API 응답 확인**: DeepSearch API 실제 데이터 확인
2. **에러 처리 강화**: API 실패 시 대체 방안 마련
3. **성능 최적화**: 응답 시간 개선
4. **사용자 경험 개선**: 로딩 상태 표시

이제 DeepSearch API로 완전히 전환되었습니다! 🎉
