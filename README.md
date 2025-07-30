# 🚀 News GPT v2 - AI 뉴스 키워드 분석 백엔드 API

> **실시간 뉴스 트렌드 분석을 위한 AI 기반 키워드 추출 백엔드 시스템**  
> DeepSearch API와 Azure OpenAI GPT-4o를 활용한 지능형 뉴스 분석 API 서버

[![Python](https://img.shields.io/badge/Python-3.11.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 목차

- [🎯 프로젝트 개요](#-프로젝트-개요)
- [⚡ 주요 기능](#-주요-기능)
- [🏗️ 시스템 아키텍처](#️-시스템-아키텍처)
- [🚀 빠른 시작](#-빠른-시작)
- [📁 프로젝트 구조](#-프로젝트-구조)
- [🔧 API 문서](#-api-문서)
- [🛠️ 개발 환경 설정](#️-개발-환경-설정)
- [📊 성능 지표](#-성능-지표)
- [🔍 사용 예시](#-사용-예시)
- [🚨 문제 해결](#-문제-해결)
- [📈 로드맵](#-로드맵)

## 🎯 프로젝트 개요

News GPT v2 Backend는 **실시간 뉴스 트렌드 분석**을 위한 AI 기반 키워드 추출 API 서버입니다. DeepSearch API를 통해 국내외 기술 뉴스를 수집하고, Azure OpenAI GPT-4o 모델을 활용하여 핵심 키워드를 자동으로 추출하는 RESTful API를 제공합니다.

### 🌟 핵심 가치

- **⚡ 실시간 분석**: 최신 뉴스의 키워드를 즉시 추출
- **🌍 글로벌 뉴스**: 국내외 기술 뉴스 동시 분석
- **🧠 AI 기반**: GPT-4o 모델을 활용한 정확한 키워드 추출
- **🔌 RESTful API**: 표준화된 API 인터페이스
- **📊 트렌드 분석**: 주간별 키워드 트렌드 분석

### 🎨 프론트엔드 분리

> **프론트엔드는 별도 저장소로 분리되었습니다**  
> 웹 인터페이스와 사용자 경험 관련 기능은 다음 저장소를 참조하세요:
> 
> **🌐 [News GPT Frontend](https://github.com/J1STAR/news-gpt-frontend)**
> - 실시간 키워드 시각화
> - AI 챗봇 인터페이스
> - 트렌딩 페이지

## ⚡ 주요 기능

### 📰 뉴스 수집 및 분석 API
- **실시간 뉴스 수집**: DeepSearch API를 통한 최신 기술 뉴스 수집
- **AI 키워드 추출**: GPT-4o 모델 기반 핵심 키워드 자동 추출
- **트렌드 분석**: 주간별 키워드 트렌드 패턴 분석
- **국내외 분석**: 한국어/영어 뉴스 동시 처리

### 🔧 백엔드 서비스
- **RESTful API**: 체계적인 API 엔드포인트 제공
- **자동화 스크립트**: 원클릭 설치 및 실행
- **캐싱 시스템**: 고성능 메모리 기반 캐싱
- **로깅 시스템**: 상세한 작업 로그 및 모니터링
- **스케줄러**: 백그라운드 작업 자동화

### 🔌 API 기능
- **키워드 추출 API**: 주간별 핵심 키워드 추출
- **기사 검색 API**: 키워드별 관련 기사 검색
- **AI 챗봇 API**: 키워드 기반 상세 분석
- **트렌딩 API**: 실시간 트렌드 데이터
- **구독 API**: 키워드 알림 서비스

## 🏗️ 시스템 아키텍처

```
+---------------------+
|      Frontend       |
|   (Separate Repo)   |
+----------+----------+
           |
           | HTTP Request
           v
+---------------------+      +---------------------+
|    FastAPI Server   |----->|    External APIs    |
| (News GPT Backend)  |      | - DeepSearch API    |
+----------+----------+      | - Azure OpenAI      |
           |                 +---------------------+
           |
           v
+---------------------+
| Internal Components |
| - Memory Cache      |
| - BG Scheduler      |
+---------------------+
```

### 🔄 데이터 플로우

1.  **뉴스 수집** (1-3초): DeepSearch API → 기술 뉴스 수집
2.  **키워드 추출** (1-2초): GPT-4o → 핵심 키워드 추출
3.  **캐싱** (즉시): 메모리 캐시에 결과 저장
4.  **관련 기사** (1-2초): 키워드 기반 관련 기사 검색
5.  **API 응답**: JSON 형태로 결과 반환

## 🚀 빠른 시작

### 1️⃣ 프로젝트 클론
```bash
git clone https://github.com/nnfct/news_gpt_v2.git
cd news_gpt_v2
```

### 2️⃣ 자동 환경 설정

**Windows (권장)**
```cmd
setup.bat
```

**macOS/Linux**
```bash
python setup.py
```

**수동 설정**
```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 3️⃣ 환경 변수 설정
```bash
# .env.template을 복사하여 .env 생성
cp .env.template .env

# .env 파일 편집
# Azure OpenAI 설정
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint

# DeepSearch API 설정
DEEPSEARCH_API_KEY=your_deepsearch_api_key
```

### 4️⃣ 서버 실행
```bash
# 간편 실행
start_server.bat  # Windows
./start_server.ps1  # PowerShell

# 수동 실행
python main.py
```

### 5️⃣ API 서버 접속
```
http://localhost:8000
```

### 6️⃣ 프론트엔드 연결
```bash
# 프론트엔드 저장소 클론
git clone https://github.com/J1STAR/news-gpt-frontend.git
cd news-gpt-frontend

# 프론트엔드 실행 (별도 저장소의 README 참조)
```

## 📁 프로젝트 구조

```
news_gpt_v2/
├── 🚀 핵심 파일
│   ├── main.py                    # FastAPI 메인 서버
│   └── requirements.txt           # Python 의존성
│
├── 🔧 API 및 서비스
│   ├── api/
│   │   ├── api_router.py          # API 라우터
│   │   └── v1/
│   │       ├── api_v1_router.py   # v1 API 라우터
│   │       └── endpoints/
│   │           ├── keywords.py     # 키워드 관련 API
│   │           ├── analysis.py     # 분석 API
│   │           ├── chat.py         # 챗봇 API
│   │           └── subscription.py # 구독 API
│   │
│   ├── services/
│   │   ├── deepsearch_service.py  # DeepSearch API 서비스
│   │   ├── openai_service.py      # OpenAI API 서비스
│   │   ├── trending_service.py    # 트렌딩 서비스
│   │   ├── email_service.py       # 이메일 서비스
│   │   └── sample_service.py      # 샘플 데이터 서비스
│   │
│   ├── core/
│   │   ├── config.py              # 설정 관리
│   │   └── schemas.py             # 데이터 스키마
│   │
│   └── utils/
│       └── helpers.py             # 유틸리티 함수
│
├── 📚 문서
│   ├── docs/                      # 상세 문서
│   ├── PROJECT_REPORT.md          # 프로젝트 보고서
│   └── requirements.md            # 요구사항 문서
│
├── ⚙️ 설정 파일
│   ├── pyproject.toml             # 프로젝트 설정
│   ├── .env.template              # 환경 변수 템플릿
│   └── .gitignore                 # Git 무시 파일
│
├── 🛠️ 실행 스크립트
│   ├── setup.py                   # 크로스 플랫폼 설치
│   ├── setup.bat                  # Windows 설치
│   ├── start_server.bat           # Windows 서버 실행
│   └── start_server.ps1           # PowerShell 서버 실행
│
└── 🗑️ Legacy 파일 (TODO: 제거 예정)
    ├── index.html                 # LEGACY: 프론트엔드 파일 (제거 예정)
    ├── analysis.html              # LEGACY: 분석 페이지 (제거 예정)
    ├── trending.html              # LEGACY: 트렌딩 페이지 (제거 예정)
    ├── news-detail.html           # LEGACY: 뉴스 상세 페이지 (제거 예정)
    └── admin.html                 # LEGACY: 관리자 페이지 (제거 예정)
```

### 🗑️ Legacy 파일 처리 계획

> **TODO**: 프론트엔드 파일들은 별도 저장소로 분리되었으므로 추후 제거 예정
> 
> - `index.html` → [news-gpt-frontend](https://github.com/J1STAR/news-gpt-frontend)로 이동
> - `analysis.html` → 프론트엔드 저장소에서 관리
> - `trending.html` → 프론트엔드 저장소에서 관리
> - `news-detail.html` → 프론트엔드 저장소에서 관리
> - `admin.html` → 프론트엔드 저장소에서 관리

## 🔧 API 문서

### 📰 키워드 분석 API

#### 주간 키워드 추출 (국내)
```http
GET /api/v1/weekly-keywords-by-date?start_date=2025-07-14&end_date=2025-07-18
```

**응답 예시:**
```json
{
  "keywords": [
    {
      "keyword": "인공지능",
      "count": 15,
      "articles": [...]
    }
  ],
  "period": "2025-07-14 ~ 2025-07-18",
  "total_keywords": 3
}
```

#### 주간 키워드 추출 (해외)
```http
GET /api/v1/global-weekly-keywords-by-date?start_date=2025-07-14&end_date=2025-07-18
```

#### 키워드별 관련 기사
```http
GET /api/v1/keyword-articles/{keyword}?start_date=2025-07-14&end_date=2025-07-18
```

### 💬 AI 챗봇 API

#### 챗봇 대화
```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "인공지능 키워드에 대해 설명해주세요",
  "context": "weekly_keywords"
}
```

### 📊 분석 API

#### 동적 키워드 분석
```http
POST /api/v1/keyword-analysis
Content-Type: application/json

{
  "keyword": "블록체인",
}
```

### 🔍 트렌딩 API

#### 실시간 트렌드 키워드
```http
GET /api/v1/trending
```

#### 국가별 트렌드 뉴스
```http
GET /api/v1/news?country=KR&keyword=tech
```

## 🛠️ 개발 환경 설정

- **가상환경**: venv
- **패키지 관리**: pip, uv
- **API 테스트**: Postman, curl

### 환경 변수

| 변수명 | 설명 | 필수 | 예시 |
|--------|------|------|------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API 키 | ✅ | `sk-...` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI 엔드포인트 | ✅ | `https://...` |
| `DEEPSEARCH_API_KEY` | DeepSearch API 키 | ✅ | `ds_...` |
| `AZURE_SEARCH_API_KEY` | Azure Search API 키 | ❌ | `...` |
| `AZURE_SEARCH_ENDPOINT` | Azure Search 엔드포인트 | ❌ | `https://...` |

## 📊 성능 지표

### ⚡ 응답 시간
- **초기 로딩**: 1-2초
- **키워드 추출**: 3-5초
- **관련 기사 검색**: 1-2초
- **캐시 히트**: 0.1초 이내


## 🔍 사용 예시

### 1. API 직접 호출

```bash
# 주간 키워드 조회
curl "http://localhost:8000/api/v1/weekly-keywords-by-date?start_date=2025-07-14&end_date=2025-07-18"

# 키워드별 기사 검색
curl "http://localhost:8000/api/v1/keyword-articles/인공지능?start_date=2025-07-14&end_date=2025-07-18"

# AI 챗봇 대화
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "인공지능 트렌드를 분석해주세요"}'

# 트렌딩 키워드 조회
curl "http://localhost:8000/api/v1/trending"
```

### 2. 개발자 도구

```bash
# 서버 상태 확인
curl "http://localhost:8000/health"

# API 문서 확인
# 브라우저에서 http://localhost:8000/docs 접속
```

### 3. 프론트엔드 연동

```javascript
// 프론트엔드에서 API 호출 예시
const response = await fetch('http://localhost:8000/api/v1/weekly-keywords-by-date?start_date=2025-07-14&end_date=2025-07-18');
const data = await response.json();
console.log(data.keywords);
```

## 📈 로드맵

### 🎯 단기 목표 (1-2개월)
- [ ] Redis 캐싱 시스템 도입
- [ ] 키워드 알림 웹훅 기능

### 🚀 중기 목표 (3-6개월)
- [ ] 다국어 지원 (영어, 일본어, 중국어)
- [ ] 고급 분석 기능 (감정 분석, 영향도 분석)
- [ ] 실시간 웹소켓 API
- [ ] 머신러닝 모델 고도화
- [ ] 클라우드 배포 자동화 (Docker, Kubernetes)

### 🗑️ Legacy 정리 계획
- [ ] 프론트엔드 파일 제거 (HTML, CSS, JS)
- [ ] 정적 파일 서빙 기능 제거
- [ ] 순수 API 서버로 전환
- [ ] 문서 업데이트

## 🤝 기여하기

1. **Fork** 프로젝트
2. **Feature branch** 생성 (`git checkout -b feature/AmazingFeature`)
3. **Commit** 변경사항 (`git commit -m 'Add some AmazingFeature'`)
4. **Push** 브랜치 (`git push origin feature/AmazingFeature`)
5. **Pull Request** 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 문의 및 지원

- **Backend Repository**: [GitHub](https://github.com/nnfct/news_gpt_v2)
- **Frontend Repository**: [GitHub](https://github.com/J1STAR/news-gpt-frontend)
- **Issues**: [GitHub Issues](https://github.com/nnfct/news_gpt_v2/issues)

---

<div align="center">

**News GPT v2 Backend** - AI 뉴스 키워드 분석 API 서버

[![GitHub stars](https://img.shields.io/github/stars/nnfct/news_gpt_v2?style=social)](https://github.com/nnfct/news_gpt_v2/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/nnfct/news_gpt_v2?style=social)](https://github.com/nnfct/news_gpt_v2/network)
[![GitHub issues](https://img.shields.io/github/issues/nnfct/news_gpt_v2)](https://github.com/nnfct/news_gpt_v2/issues)

**🌐 Frontend**: [News GPT Frontend](https://github.com/J1STAR/news-gpt-frontend)

</div>
