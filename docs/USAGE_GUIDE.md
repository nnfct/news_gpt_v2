# 🚀 DeepSearch API 실사용 가이드

## 📋 시스템 요구사항
- Windows 10/11
- Python 3.11.9
- PowerShell 실행 권한

## 🛠️ 설치 및 실행 방법

### 1단계: 프로젝트 폴더로 이동
```bash
cd C:\Users\USER\Documents\GitHub\news_gpt_v2
```

### 2단계: 서버 시작
```bash
# 배치 파일 실행 (권장)
.\start_deepsearch_server.bat

# 또는 수동 실행
.\venv_new\Scripts\activate
python main.py
```

### 3단계: 웹 브라우저에서 접속
```
http://localhost:8003
```

## 🔧 설정 정보

### 환경 변수 (.env 파일)
```env
# DeepSearch API 설정
DEEPSEARCH_API_KEY=5e0b0dba14d846918383174f356dd683
```

### 서버 설정
- **포트**: 8003
- **호스트**: 0.0.0.0 (모든 IP에서 접근 가능)
- **가상환경**: `venv_new`

## 🎯 주요 기능

### 1. 주간 뉴스 요약
- **1주차**: 2025-07-01 ~ 2025-07-05
- **2주차**: 2025-07-06 ~ 2025-07-13  
- **3주차**: 2025-07-14 ~ 2025-07-18

### 2. 키워드 기반 기사 검색
- DeepSearch API 활용
- 날짜 범위별 필터링
- 실시간 뉴스 데이터

## 🔍 API 엔드포인트

### 주요 엔드포인트
- `GET /` - 메인 페이지
- `GET /api/weekly-summary` - 주간 요약
- `GET /api/weekly-keywords-by-date` - 날짜별 키워드
- `GET /api/articles/{keyword}` - 키워드별 기사

### DeepSearch API 설정
- **Base URL**: `https://api-v2.deepsearch.com/v1/articles/economy,tech`
- **인증**: API Key 방식
- **응답 포맷**: JSON
- **카테고리**: 경제(economy), 기술(tech)

## 🚨 문제 해결

### 포트 충돌 시
1. `main.py` 파일에서 포트 변경
2. `start_deepsearch_server.bat` 파일에서 포트 정보 수정

### 패키지 오류 시
```bash
.\venv_new\Scripts\activate
pip install -r requirements.txt
```

### 권한 오류 시
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📊 개발 정보

### 브랜치 정보
- **현재 브랜치**: `deepsearch-api-test`
- **메인 브랜치**: 영향 없음
- **변경사항**: DeepSearch API 통합

### 주요 변경사항
1. **API 교체**: Naver API → DeepSearch API
2. **환경 변수**: `DEEPSEARCH_API_KEY` 추가
3. **함수 업데이트**: `get_current_week_news_from_deepsearch`
4. **에러 처리**: 글로벌 예외 처리 추가

## 🎉 성공 확인

서버가 정상적으로 시작되면 다음과 같은 메시지를 확인할 수 있습니다:
```
INFO:     Uvicorn running on http://0.0.0.0:8003 (Press CTRL+C to quit)
```

웹 브라우저에서 `http://localhost:8003`에 접속하여 주간 뉴스 요약 시스템을 사용할 수 있습니다.
