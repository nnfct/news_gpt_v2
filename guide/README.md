# � News GPT v2 - AI 뉴스 키워드 분석 플랫폼

> Azure OpenAI와 Azure AI Search를 활용한 실시간 뉴스 키워드 분석 및 트렌드 분석 플랫폼

## 📋 프로젝트 개요

News GPT v2는 Azure 클라우드 서비스를 기반으로 한 AI 기반 뉴스 분석 플랫폼입니다. 네이버 뉴스 API를 통해 실시간 뉴스를 수집하고, Azure OpenAI GPT-4o 모델을 활용하여 키워드 분석 및 트렌드 분석을 제공합니다.

### 🎯 주요 기능

- **📰 실시간 뉴스 수집**: 네이버 뉴스 API를 통한 29개 IT/기술 키워드 기반 뉴스 자동 수집
- **🔍 주간 키워드 분석**: AI 기반 주간 TOP 3 키워드 추출 및 빈도 분석
- **🤖 다각도 분석**: 사회, 경제, IT/과학, 생활/문화, 세계 관점별 키워드 분석
- **� 지능형 챗봇**: Azure OpenAI 기반 실시간 뉴스 분석 챗봇
- **� 벡터 검색**: Azure AI Search를 활용한 의미 기반 뉴스 검색

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  FastAPI        │    │  Azure Services │
│   (HTML/JS)     │◄──►│  Server         │◄──►│                 │
│                 │    │  (Port 8000)    │    │ Azure OpenAI    │
└─────────────────┘    └─────────────────┘    │ Azure AI Search │
                                              │ Naver News API  │
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
- **News API**: Naver News Search API
- **Environment**: Python venv, python-dotenv

**Frontend**
- **Core**: HTML5, CSS3, JavaScript (ES6+)
- **Design**: 반응형 웹 디자인 (Inter 폰트)
- **API**: Fetch API, RESTful 통신

**Cloud Infrastructure**
- **Azure OpenAI Service**: GPT-4o 모델 배포
- **Azure AI Search**: 벡터 인덱스 및 하이브리드 검색
- **Local Execution**: FastAPI 서버 로컬 실행

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

3. **Naver Developers**
   - 네이버 검색 API (뉴스) 등록

### 3. 환경변수 설정

`.env` 파일을 수정하여 발급받은 API 키를 설정하세요:

```bash
# Azure OpenAI 설정
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/

# Azure AI Search 설정
AZURE_SEARCH_API_KEY=your_azure_search_api_key_here
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_INDEX=news_index

# 네이버 뉴스 API 설정
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here
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
| `/weekly-summary` | GET | 주간 키워드 요약 |
| `/weekly-keywords` | GET | 주간 TOP 3 키워드 |
| `/section-analysis/{section}` | GET | 섹션별 키워드 분석 |
| `/chat` | POST | AI 챗봇 대화 |
| `/industry-analysis` | POST | 산업별 분석 |
| `/keyword-articles` | GET | 키워드별 관련 기사 |

### API 사용 예시

```bash
# 주간 키워드 조회
curl http://localhost:8000/weekly-keywords

# 챗봇 대화
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "인공지능 뉴스 분석해줘"}'

# 키워드별 기사 조회
curl "http://localhost:8000/keyword-articles?keyword=인공지능"
```

## 🔧 프로젝트 구조

```
news_gpt_v2/
├── .env                    # 환경변수 설정
├── .venv/                  # Python 가상환경
├── main.py                 # FastAPI 메인 서버
├── index.html              # 웹 인터페이스
├── requirements.txt        # Python 의존성
├── run_analysis.py         # 뉴스 분석 스크립트
├── check_indexes.py        # Azure AI Search 인덱스 확인
├── check_search_data.py    # 저장된 데이터 확인
├── upload_test_articles.py # 테스트 데이터 업로드
├── upload_summary.py       # 주간 요약 업로드
├── start_server.bat        # Windows 서버 실행 스크립트
├── start_server.ps1        # PowerShell 서버 실행 스크립트
└── PROJECT_REPORT.md       # 프로젝트 완료 보고서
```

## 🧪 분석 스크립트 실행

### 1. 뉴스 수집 및 키워드 분석

```bash
# 7일치 뉴스 수집 및 분석 (29개 키워드 기반)
python run_analysis.py
```

이 스크립트는 다음 작업을 수행합니다:
- 29개 IT/기술 키워드로 네이버 뉴스 검색
- 중복 제거 후 Azure AI Search에 업로드
- Azure OpenAI로 키워드 추출 및 빈도 분석
- 주간 TOP 3 키워드 선정 및 요약 생성

### 2. 개별 스크립트 실행

```bash
# 주간 요약만 업로드
python upload_summary.py

# 테스트 기사 5개 업로드
python upload_test_articles.py

# 현재 Azure AI Search 상태 확인
python check_search_data.py
```

## 📊 현재 데이터 상태

### 2025년 7월 3주차 분석 결과

**TOP 3 키워드**:
1. **인공지능** (12회 언급)
2. **반도체** (8회 언급)  
3. **AI** (8회 언급)

**저장된 데이터**:
- 총 20개 문서 (카드 뉴스 4개 + 일반 뉴스 16개)
- Azure AI Search `news_index`에 저장
- 벡터 임베딩 기반 의미 검색 지원

## � 문제 해결

### 자주 발생하는 문제

#### 1. 환경변수 오류
```bash
# .env 파일 확인
cat .env

# 환경변수 로딩 테스트
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('AZURE_OPENAI_API_KEY exists:', bool(os.getenv('AZURE_OPENAI_API_KEY')))"
```

#### 2. Azure AI Search 연결 오류
```bash
# 인덱스 상태 확인
python check_indexes.py

# 데이터 상태 확인  
python check_search_data.py
```

#### 3. 네이버 API 요청 제한 (429 에러)
- 요청 간격 조정: `run_analysis.py`에서 `time.sleep()` 값 증가
- API 할당량 확인: 네이버 개발자센터에서 사용량 모니터링

#### 4. 서버 실행 오류
```bash
# 포트 8000 사용 확인
netstat -an | findstr :8000  # Windows
lsof -i :8000               # macOS/Linux

# 가상환경 재활성화
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # macOS/Linux
```

## 📈 성능 최적화 및 모니터링

### Azure 서비스 최적화
- **Azure OpenAI**: 요청당 토큰 수 제한으로 비용 최적화
- **Azure AI Search**: 인덱스 크기 및 검색 성능 모니터링
- **API 요청**: 네이버 API 사용량 및 응답 시간 추적

### 로컬 서버 최적화
- **메모리 사용량**: 대용량 뉴스 처리 시 배치 크기 조정
- **API 응답 시간**: FastAPI 비동기 처리로 성능 향상
- **캐싱**: 자주 요청되는 키워드 결과 메모리 캐시

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
4. 개발 및 테스트
5. Pull Request 제출

### 코딩 컨벤션
- **Python**: PEP 8 준수, Black 포매터 사용
- **JavaScript**: ES6+ 표준, Prettier 사용
- **API**: RESTful 설계 원칙
- **커밋 메시지**: Conventional Commits 형식

### 새로운 기능 추가 가이드
1. **새로운 키워드 추가**: `run_analysis.py`의 `tech_keywords` 리스트 수정
2. **새로운 분석 관점 추가**: `main.py`의 섹션별 분석 로직 확장
3. **UI 개선**: `index.html`의 CSS 및 JavaScript 수정

## 📊 향후 개발 계획

### Phase 1 (완료)
- ✅ Azure OpenAI 연동
- ✅ Azure AI Search 구현
- ✅ 네이버 뉴스 API 연동
- ✅ 기본 웹 인터페이스
- ✅ 주간 키워드 분석

### Phase 2 (계획)
- 🔄 실시간 뉴스 수집 스케줄러
- 🔄 키워드 트렌드 시각화 (Chart.js)
- 🔄 사용자 피드백 시스템
- 🔄 다국어 지원 (영어)

### Phase 3 (계획)
- � 감정 분석 (긍정/부정/중립)
- 📋 소셜 미디어 데이터 연동
- 📋 개인화된 뉴스 추천
- 📋 모바일 앱 개발

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
- **Azure OpenAI**: https://azure.microsoft.com/ko-kr/products/ai-services/openai-service
- **Azure AI Search**: https://azure.microsoft.com/ko-kr/products/ai-services/ai-search
- **네이버 개발자센터**: https://developers.naver.com/

---

**⭐ 이 프로젝트가 도움이 되었다면 GitHub에서 스타를 눌러주세요!**

## 📸 스크린샷

### 메인 대시보드
![메인 화면](https://via.placeholder.com/800x400/667eea/white?text=News+GPT+v2+Main+Dashboard)

### 키워드 분석
![키워드 분석](https://via.placeholder.com/800x400/764ba2/white?text=Keyword+Analysis+View)

### AI 챗봇
![AI 챗봇](https://via.placeholder.com/800x400/667eea/white?text=AI+Chatbot+Interface)