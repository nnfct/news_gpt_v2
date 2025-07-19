# 🚀 News GPT v2 - AI 뉴스 키워드 분석 플랫폼

> DeepSearch API와 Azure OpenAI를 활용한 실시간 뉴스 키워드 분석 및 트렌드 분석 플랫폼

## 📋 프로젝트 개요

News GPT v2는 Azure 클라우드 서비스와 DeepSearch API를 기반으로 한 AI 기반 뉴스 분석 플랫폼입니다. DeepSearch 뉴스 API v2를 통해 실시간 뉴스를 수집하고, Azure OpenAI GPT-4o 모델을 활용하여 키워드 분석 및 트렌드 분석을 제공합니다.

### 🎯 주요 기능

- **📰 실시간 뉴스 수집**: DeepSearch API v2를 통한 IT/기술 키워드 기반 뉴스 자동 수집
- **🔍 키워드 분석**: AI 기반 주간 TOP 5 키워드 추출 및 빈도 분석
- **🤖 다각도 분석**: 사회, 경제, IT/과학, 생활/문화, 세계 관점별 키워드 분석
- **💬 지능형 챗봇**: Azure OpenAI 기반 실시간 뉴스 분석 챗봇
- **🔎 벡터 검색**: Azure AI Search를 활용한 의미 기반 뉴스 검색
- **📊 산업별 분석**: 정반대 관점을 포함한 균형잡힌 산업 분석

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  FastAPI        │    │  Azure Services │
│   (HTML/JS)     │◄──►│  Server         │◄──►│                 │
│                 │    │  (Port 8000)    │    │ Azure OpenAI    │
└─────────────────┘    └─────────────────┘    │ Azure AI Search │
                                              │DeepSearch API v2│
┌─────────────────┐    ┌─────────────────┐    └─────────────────┘
│   Analysis      │    │   Data Flow     │
│   Dashboard     │    │   Processing    │
└─────────────────┘    └─────────────────┘
```

### 🔧 기술 스택

**Backend**
- **Framework**: FastAPI (Python 3.11+)
- **AI Engine**: Azure OpenAI (GPT-4o, text-embedding-3-large)
- **Vector Database**: Azure AI Search
- **News API**: DeepSearch News API v2
- **Environment**: Python venv, python-dotenv

**Frontend**
- **Core**: HTML5, CSS3, JavaScript (ES6+)
- **Design**: 반응형 웹 디자인 (Inter 폰트)
- **API**: Fetch API, RESTful 통신

**Cloud Infrastructure**
- **Azure OpenAI Service**: GPT-4o 모델 배포
- **Azure AI Search**: 벡터 인덱스 및 하이브리드 검색
- **Local Execution**: FastAPI 서버 로컬 실행

**Dependencies**
- **fastapi**: 웹 프레임워크
- **uvicorn**: ASGI 서버
- **openai**: Azure OpenAI 클라이언트
- **azure-search-documents**: Azure AI Search 클라이언트
- **requests**: HTTP 클라이언트
- **python-dotenv**: 환경변수 관리

## 🚀 빠른 시작

### 1. 저장소 클론 및 환경 설정

```bash
# 저장소 클론
git clone https://github.com/nnfct/news_gpt_v2.git
cd news_gpt_v2

# Python 가상환경 생성 및 활성화
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. Azure 서비스 설정

Azure Portal에서 다음 서비스를 생성하고 API 키를 발급받으세요:

1. **Azure OpenAI Service**
   - GPT-4o 모델 배포
   - text-embedding-3-large 모델 배포 (선택사항)

2. **Azure AI Search**
   - 검색 서비스 생성
   - 인덱스: `news_index` 생성

3. **DeepSearch News API**
   - 뉴스 검색 API 등록 및 키 발급

### 3. 환경변수 설정

`.env` 파일을 생성하고 발급받은 API 키를 설정하세요:

```bash
# Azure OpenAI 설정
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/

# Azure AI Search 설정
AZURE_SEARCH_API_KEY=your_azure_search_api_key_here
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX=news_index

# DeepSearch 뉴스 API 설정
DEEPSEARCH_API_KEY=your_deepsearch_api_key_here
```

### 4. 데이터 초기화 및 테스트

```bash
# Azure AI Search 인덱스 확인
python check_indexes.py

# 테스트 기사 업로드
python upload_test_articles.py

# 저장된 데이터 확인
python check_search_data.py
```

### 5. 서버 실행

**방법 1: PowerShell 스크립트 (Windows)**
```powershell
.\start_server.ps1
```

**방법 2: 배치 파일 (Windows)**
```cmd
start_server.bat
```

**방법 3: 직접 실행**
```bash
python main.py
```

### 6. 웹 인터페이스 접속

브라우저에서 http://localhost:8000 에 접속하여 뉴스 분석 플랫폼을 이용하세요.

## 📖 API 엔드포인트

### 주요 API

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/` | GET | 메인 웹 페이지 |
| `/keyword-articles` | GET | 키워드별 관련 기사 검색 |
| `/api/articles` | GET | 기사 요약본 반환 |
| `/api/keywords` | GET | 주간 TOP 5 키워드 분석 |
| `/chat` | POST | AI 챗봇 대화 |
| `/weekly-keywords` | GET | 주간 TOP 3 키워드 |
| `/industry-analysis` | POST | 산업별 분석 (정반대 관점 포함) |
| `/keyword-analysis` | POST | 동적 키워드 분석 |

### API 사용 예시

```bash
# 주간 키워드 조회
curl http://localhost:8000/weekly-keywords

# 챗봇 대화
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "인공지능 뉴스 분석해줘"}'

# 키워드별 기사 조회
curl "http://localhost:8000/keyword-articles?keyword=AI&start_date=2025-07-14&end_date=2025-07-18"

# 산업별 분석
curl -X POST http://localhost:8000/industry-analysis \
  -H "Content-Type: application/json" \
  -d '{"industry": "IT/과학", "keyword": "인공지능"}'
```

## 🔧 프로젝트 구조

```
news_gpt_v2/
├── .env                         # 환경변수 설정
├── .venv/                       # Python 가상환경
├── main.py                      # FastAPI 메인 서버
├── index.html                   # 웹 인터페이스
├── index_new.html               # 새 웹 인터페이스
├── requirements.txt             # Python 의존성
├── 
├── # 분석 및 실행 스크립트
├── run_analysis.py              # 뉴스 분석 스크립트
├── run_analysis_deepsearch.py   # DeepSearch API 분석 스크립트
├── keyword_aggregation.py       # 키워드 집계 스크립트
├── 
├── # 데이터 확인 및 테스트
├── check_indexes.py             # Azure AI Search 인덱스 확인
├── check_search_data.py         # 저장된 데이터 확인
├── check_weekly_api.py          # 주차별 API 응답 확인
├── debug_deepsearch.py          # DeepSearch API 디버그
├── test_deepsearch_endpoint.py  # DeepSearch 엔드포인트 테스트
├── 
├── # 데이터 업로드 스크립트
├── upload_test_articles.py      # 테스트 데이터 업로드
├── upload_summary.py            # 주간 요약 업로드
├── recreate_index.py            # 인덱스 재생성
├── 
├── # 서버 실행 스크립트
├── start_server.bat             # Windows 배치 실행
├── start_server.ps1             # PowerShell 실행
├── start_uvicorn.ps1            # Uvicorn 실행
├── start_deepsearch_server.bat  # DeepSearch 서버 실행
├── setup_and_run.ps1            # 설정 및 실행
├── run_system_python.ps1        # 시스템 Python 실행
├── 
├── # 문서화
├── README.md                    # 프로젝트 메인 문서 (현재 파일)
├── DEEPSEARCH_GUIDE.md          # DeepSearch API 가이드
├── USAGE_GUIDE.md               # 사용법 가이드
├── PROJECT_REPORT.md            # 프로젝트 완료 보고서
├── requirements.md              # 요구사항 명세서
├── design.md                    # 설계 문서
├── task.md                      # 작업 계획서
├── error_history.md             # 오류 기록
├── 
├── # 유틸리티
├── error_logger.py              # 오류 로깅 유틸리티
├── 
├── # 백업 및 참조
├── backup/                      # HTML 백업 파일들
│   ├── index_backup_current.html
│   ├── index_backup_original.html
│   └── index_backup.html
├── reference/                   # 참조용 파일들
│   ├── index (1).html
│   └── main.py
├── guide/                       # 가이드 문서들
│   ├── design.md
│   ├── README.md
│   └── task.md
└── __pycache__/                 # Python 캐시 파일들
```

## 🧪 분석 스크립트 실행

### 1. 뉴스 수집 및 키워드 분석

```bash
# DeepSearch API 기반 뉴스 수집 및 분석
python run_analysis_deepsearch.py

# 기존 분석 스크립트 (레거시)
python run_analysis.py

# 키워드 집계 스크립트
python keyword_aggregation.py
```

이 스크립트들은 다음 작업을 수행합니다:
- IT/기술 키워드로 DeepSearch API를 통한 뉴스 검색
- 중복 제거 후 Azure AI Search에 업로드
- Azure OpenAI로 키워드 추출 및 빈도 분석
- 주간 TOP 5 키워드 선정 및 요약 생성

### 2. 데이터 확인 및 테스트

```bash
# Azure AI Search 인덱스 상태 확인
python check_indexes.py

# 저장된 데이터 확인
python check_search_data.py

# 주차별 API 응답 확인
python check_weekly_api.py

# DeepSearch API 디버그
python debug_deepsearch.py

# DeepSearch 엔드포인트 테스트
python test_deepsearch_endpoint.py
```

### 3. 데이터 업로드 및 초기화

```bash
# 테스트 기사 5개 업로드
python upload_test_articles.py

# 주간 요약만 업로드
python upload_summary.py

# 인덱스 재생성
python recreate_index.py
```

## 📊 현재 데이터 상태

### 2025년 7월 3주차 분석 결과

**TOP 5 키워드** (GPT-4o 기반 분석):
1. **인공지능** (25회 언급)
2. **반도체** (20회 언급)  
3. **클라우드** (18회 언급)
4. **메타버스** (15회 언급)
5. **블록체인** (12회 언급)

**저장된 데이터**:
- DeepSearch API v2를 통한 실시간 뉴스 수집
- Azure AI Search `news_index`에 저장
- 벡터 임베딩 기반 의미 검색 지원
- GPT-4o 기반 키워드 추출 및 분석

**현재 브랜치**: `deepsearch-api-test`
- DeepSearch API v2로 완전 전환 완료
- Naver API에서 마이그레이션 완료

## 🔧 문제 해결

### 자주 발생하는 문제

#### 1. 환경변수 오류
```bash
# .env 파일 확인
Get-Content .env  # PowerShell
type .env        # CMD

# 환경변수 로딩 테스트
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DEEPSEARCH_API_KEY exists:', bool(os.getenv('DEEPSEARCH_API_KEY')))"
```

#### 2. Azure AI Search 연결 오류
```bash
# 인덱스 상태 확인
python check_indexes.py

# 데이터 상태 확인  
python check_search_data.py
```

#### 3. DeepSearch API 요청 제한
- 요청 간격 조정: `main.py`에서 `time.sleep()` 값 증가
- API 할당량 확인: DeepSearch 개발자센터에서 사용량 모니터링
- 재시도 로직 활용: 자동 재시도 메커니즘 내장

#### 4. 서버 실행 오류
```powershell
# 포트 8000 사용 확인
netstat -an | findstr :8000

# 가상환경 재활성화
.venv\Scripts\activate

# 서버 직접 실행
python main.py

# 또는 PowerShell 스크립트 사용
.\start_server.ps1
```

#### 5. 챗봇 기능 문제
```bash
# 챗봇 엔드포인트 테스트
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"question\": \"테스트\"}"

# Azure OpenAI 연결 확인
python -c "from openai import AzureOpenAI; print('Azure OpenAI 연결 가능')"
```

## 📈 성능 최적화 및 모니터링

### Azure 서비스 최적화
- **Azure OpenAI**: 요청당 토큰 수 제한으로 비용 최적화 (GPT-4o 모델 사용)
- **Azure AI Search**: 인덱스 크기 및 검색 성능 모니터링
- **API 요청**: DeepSearch API 사용량 및 응답 시간 추적

### 로컬 서버 최적화
- **메모리 사용량**: 대용량 뉴스 처리 시 배치 크기 조정
- **API 응답 시간**: FastAPI 비동기 처리로 성능 향상
- **캐싱**: 자주 요청되는 키워드 결과 메모리 캐시
- **재시도 메커니즘**: API 실패 시 자동 재시도 (최대 3회)

### 모니터링 도구
- **로깅**: 구조화된 로그 기록 (`error_logger.py`)
- **오류 추적**: 자동 오류 기록 (`error_history.md`)
- **API 테스트**: 다양한 테스트 스크립트 제공

## 🔐 보안 고려사항

### API 키 관리
- `.env` 파일은 절대 Git에 커밋하지 마세요
- 프로덕션 환경에서는 Azure Key Vault 사용 권장
- API 키 로테이션 정기적 수행

### CORS 정책
현재 모든 오리진 허용 설정이지만, 프로덕션에서는 제한 필요:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 🤝 기여 및 개발 가이드

### 개발 환경 설정
1. Fork 저장소
2. 로컬에 클론: `git clone https://github.com/yourusername/news_gpt_v2.git`
3. 브랜치 생성: `git checkout -b feature/new-feature`
4. 가상환경 설정: `python -m venv .venv` && `.venv\Scripts\activate`
5. 의존성 설치: `pip install -r requirements.txt`
6. 환경변수 설정: `.env` 파일 생성
7. 개발 및 테스트
8. Pull Request 제출

### 코딩 컨벤션
- **Python**: PEP 8 준수, Black 포매터 사용
- **JavaScript**: ES6+ 표준, Prettier 사용
- **API**: RESTful 설계 원칙
- **커밋 메시지**: Conventional Commits 형식

### 새로운 기능 추가 가이드
1. **새로운 API 엔드포인트 추가**: `main.py`에 FastAPI 라우터 추가
2. **새로운 분석 관점 추가**: 산업별 분석 로직 확장
3. **UI 개선**: `index.html` 또는 `index_new.html` 수정
4. **새로운 키워드 추가**: DeepSearch API 검색 키워드 확장

### 테스트 방법
```bash
# API 엔드포인트 테스트
python check_weekly_api.py

# DeepSearch API 테스트
python debug_deepsearch.py

# 전체 시스템 테스트
python test_deepsearch_endpoint.py
```

## 📊 향후 개발 계획

### Phase 1 (완료 ✅)
- ✅ Azure OpenAI 연동 (GPT-4o)
- ✅ Azure AI Search 구현
- ✅ DeepSearch API v2 연동 (Naver API에서 마이그레이션)
- ✅ 기본 웹 인터페이스 (`index.html`)
- ✅ 주간 키워드 분석 (TOP 5)
- ✅ AI 챗봇 기능
- ✅ 산업별 분석 (정반대 관점 포함)
- ✅ 동적 키워드 분석

### Phase 2 (계획중 🔄)
- 🔄 실시간 뉴스 수집 스케줄러
- 🔄 키워드 트렌드 시각화 (Chart.js)
- 🔄 사용자 피드백 시스템
- 🔄 다국어 지원 (영어)
- 🔄 새로운 웹 인터페이스 완성 (`index_new.html`)

### Phase 3 (미래 계획 📋)
- 📋 감정 분석 (긍정/부정/중립)
- 📋 소셜 미디어 데이터 연동
- 📋 개인화된 뉴스 추천
- 📋 모바일 앱 개발
- 📋 실시간 알림 시스템

### 기술적 개선사항
- **성능 최적화**: 캐싱 시스템 도입
- **확장성**: 마이크로서비스 아키텍처 전환
- **보안**: Azure Key Vault 통합
- **모니터링**: Application Insights 연동

## �📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

```
MIT License

Copyright (c) 2025 News GPT v2

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 👥 개발팀

- **개발자**: nnfct
- **저장소**: https://github.com/nnfct/news_gpt_v2
- **이슈 및 문의**: GitHub Issues 페이지 활용

## 🔗 관련 링크

- **프로젝트 데모**: http://localhost:8000 (로컬 실행 시)
- **GitHub 저장소**: https://github.com/nnfct/news_gpt_v2
- **현재 브랜치**: `deepsearch-api-test`
- **Azure OpenAI**: https://azure.microsoft.com/ko-kr/products/ai-services/openai-service
- **Azure AI Search**: https://azure.microsoft.com/ko-kr/products/ai-services/ai-search
- **DeepSearch API**: https://www.deepsearch.com/ (뉴스 검색 API)

## 📋 추가 문서

- **[DeepSearch API 가이드](DEEPSEARCH_GUIDE.md)**: DeepSearch API 전환 가이드
- **[사용법 가이드](USAGE_GUIDE.md)**: 상세 사용법 및 설정
- **[프로젝트 보고서](PROJECT_REPORT.md)**: 완료된 기능 및 성과
- **[설계 문서](design.md)**: 시스템 아키텍처 및 설계
- **[작업 계획서](task.md)**: 개발 계획 및 진행 상황

---

**⭐ 이 프로젝트가 도움이 되었다면 GitHub에서 스타를 눌러주세요!**

## 📸 스크린샷 및 데모

### 메인 대시보드
- **주간 키워드 분석**: AI 기반 TOP 5 키워드 추출
- **산업별 관점**: 5가지 관점에서의 분석 제공
- **실시간 뉴스**: DeepSearch API 기반 최신 뉴스

### AI 챗봇 기능
- **산업별 분석**: 사회, 경제, IT/과학, 생활/문화, 세계 관점
- **정반대 관점**: 균형잡힌 분석을 위한 반대 의견 제시
- **동적 키워드 분석**: 클릭한 키워드에 대한 즉석 분석

### 키워드 분석
- **트렌드 분석**: 시간별 키워드 변화 추적
- **관련 기사**: 키워드별 관련 뉴스 자동 수집
- **의미 검색**: Azure AI Search 기반 벡터 검색

## 🎯 프로젝트 성과

### 기술적 성과
- **API 전환**: Naver API → DeepSearch API v2 성공적 마이그레이션
- **AI 통합**: Azure OpenAI GPT-4o 모델 안정적 운영
- **검색 성능**: Azure AI Search 벡터 검색 구현

### 기능적 성과
- **9개 API 엔드포인트**: 완전한 RESTful API 제공
- **실시간 분석**: 키워드 기반 뉴스 분석 자동화
- **다각도 분석**: 5가지 산업 관점 + 정반대 관점 제공
- **사용자 경험**: 직관적인 웹 인터페이스 및 챗봇

---

**📧 문의사항이 있으시면 GitHub Issues를 통해 연락주세요.**
**🚀 지속적인 업데이트와 개선이 진행 중입니다.**