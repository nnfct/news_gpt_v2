# 🚀 뉴스 분석 플랫폼

> AI 기반 자동화된 뉴스 분석 및 카드뉴스 생성 플랫폼

## 📋 프로젝트 개요

이 프로젝트는 뉴스 수집부터 AI 분석, 카드뉴스 생성, 챗봇 서비스까지 전 과정을 자동화한 종합 뉴스 분석 플랫폼입니다.

### 🎯 주요 기능

- **📰 자동 뉴스 수집**: 네이버, 구글 등 다양한 소스에서 실시간 뉴스 수집
- **🔍 키워드 분석**: 한국어 NLP 기반 주간 TOP 키워드 추출 및 트렌드 분석
- **🤖 AI 관점 분석**: OpenAI/Claude를 활용한 경제, 정치, 사회, 기술, 국제 관점별 분석
- **📊 카드뉴스 생성**: 템플릿 기반 자동 카드뉴스 생성
- **💬 RAG 챗봇**: 벡터 검색 기반 컨텍스트 인식 챗봇 서비스

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  API Gateway    │    │ Microservices   │
│   (HTML/JS)     │◄──►│   (Port 8000)   │◄──►│                 │
└─────────────────┘    └─────────────────┘    │ News Collector  │
                                              │ Keyword Analyzer│
┌─────────────────┐    ┌─────────────────┐    │ AI Analysis     │
│   Vector DB     │    │   Database      │    │ Chat Service    │
│   (Qdrant)      │    │ (SQLite/PG)     │    └─────────────────┘
└─────────────────┘    └─────────────────┘
```

### 🔧 기술 스택 (수정필요 / azure 위주로 )

**Backend**
- **Framework**: FastAPI (Python 3.8+)
- **Database**: SQLite (개발) / PostgreSQL (프로덕션)
- **Vector DB**: Qdrant (임베딩 검색)
- **AI**: OpenAI GPT, Claude API
- **NLP**: KoNLPy, Sentence Transformers
- **Cache**: Redis (세션 관리)

**Frontend**
- **Core**: HTML5, CSS3, JavaScript (ES6+)
- **Design**: 반응형 웹 디자인
- **API**: Fetch API, Async/Await

**Infrastructure**
- **Architecture**: 마이크로서비스
- **Containerization**: Docker
- **API Gateway**: FastAPI 기반 통합 라우팅

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd news-analysis-platform

# Python 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r backend/shared/requirements.txt
```

### 2. 환경변수 설정

```bash
# .env 파일 생성
cp backend/.env.example backend/.env

# 필수 환경변수 설정
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_claude_api_key
DATABASE_URL=sqlite:///./news_analysis.db
```

### 3. 테스트 데이터 생성

```bash
cd backend
python create_test_data.py
```

### 4. 서비스 실행

#### 옵션 1: 데모 서버 (통합)
```bash
cd backend
python demo_server.py
# 브라우저에서 http://localhost:5000 접속
```

#### 옵션 2: 개별 서비스 실행
```bash
# API Gateway
cd backend/api-gateway && python main.py  # Port 8000

# News Collector
cd backend/services/news-collector && python main.py  # Port 8001

# Keyword Analyzer  
cd backend/services/keyword-analyzer && python main.py  # Port 8002

# AI Analysis
cd backend/services/ai-analysis && python main.py  # Port 8003

# Chat Service
cd backend/services/chat-service && python main.py  # Port 8004
```

### 5. 프론트엔드 실행

```bash
# 브라우저에서 index.html 열기
open index.html  # macOS
start index.html  # Windows
```

## 📖 API 문서

### 주요 엔드포인트

#### 뉴스 관련
- `GET /api/news/recent` - 최근 뉴스 조회
- `POST /api/collect/weekly` - 주간 뉴스 수집 트리거

#### 키워드 분석
- `GET /api/keywords/weekly/{week}` - 주차별 키워드 조회
- `POST /api/analyze/keywords` - 키워드 분석 실행

#### AI 분석
- `POST /api/analyze/perspectives` - 관점별 분석 실행
- `GET /api/analysis/cards/{keyword}` - 키워드별 분석 카드 조회
- `POST /api/generate/card-news` - 카드뉴스 생성

#### 챗봇
- `POST /api/chat/query` - 챗봇 질문 처리
- `GET /api/chat/context/{session_id}` - 대화 컨텍스트 조회

#### 통합 워크플로우
- `POST /api/workflow/full-analysis` - 전체 분석 파이프라인 실행
- `GET /api/dashboard/summary` - 대시보드 요약 정보

### Swagger 문서
서비스 실행 후 다음 URL에서 상세 API 문서 확인:
- API Gateway: http://localhost:8000/docs
- 개별 서비스: http://localhost:800{1-4}/docs

## 🧪 테스트

```bash
# 단위 테스트 실행
cd backend/tests
pip install -r requirements.txt
pytest

# 특정 테스트 실행
pytest test_models.py -v
pytest test_api_gateway.py -v
```

## 📊 데이터 모델

### 주요 테이블

#### NewsArticle (뉴스 기사)
```sql
- id: 고유 식별자
- title: 제목
- content: 본문
- source: 출처 (naver, google, daum, bing)
- keywords: 추출된 키워드 (JSON)
- sentiment_score: 감정 점수 (-1.0 ~ 1.0)
- published_at: 발행일시
```

#### WeeklyKeyword (주간 키워드)
```sql
- id: 고유 식별자
- keyword: 키워드
- week_start/end: 주차 기간
- frequency: 빈도수
- trend_score: 트렌드 점수
- rank: 순위 (1-3)
```

#### AnalysisCard (분석 카드)
```sql
- id: 고유 식별자
- keyword_id: 키워드 참조
- perspective: 관점 (economy, politics, society, technology, international)
- title: 제목
- content: 분석 내용
- insights: 인사이트 (JSON)
- action_items: 행동방향 (JSON)
- confidence_score: 신뢰도 (0.0 ~ 1.0)
```

#### ChatContext (챗봇 대화)
```sql
- id: 고유 식별자
- session_id: 세션 ID
- user_query: 사용자 질문
- response: AI 응답
- retrieved_cards: 검색된 카드 (JSON)
- feedback_score: 피드백 점수 (1-5)
```

## 🔧 설정 및 커스터마이징

### AI 모델 설정
```python
# backend/services/ai-analysis/clients/ai_client_manager.py
PREFERRED_AI_PROVIDER = "openai"  # or "claude"
```

### 벡터 데이터베이스 설정
```python
# backend/services/chat-service/main.py
VECTOR_STORE_TYPE = "memory"  # or "qdrant"
EMBEDDING_PROVIDER = "openai"  # or "sentence_transformers"
```

### 키워드 분석 설정
```python
# backend/services/keyword-analyzer/analyzer/keyword_extractor.py
MAX_KEYWORDS = 3
MIN_FREQUENCY = 5
```

## 🚨 문제 해결

### 자주 발생하는 문제

#### 1. API 키 오류
```bash
# 환경변수 확인
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# .env 파일 확인
cat backend/.env
```

#### 2. 데이터베이스 오류
```bash
# 데이터베이스 재생성
rm backend/test_news.db
cd backend && python create_test_data.py
```

#### 3. 포트 충돌
```bash
# 사용 중인 포트 확인
netstat -an | grep :8000
lsof -i :8000  # macOS/Linux

# 프로세스 종료
kill -9 <PID>
```

#### 4. 의존성 문제
```bash
# 가상환경 재생성
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r backend/shared/requirements.txt
```

## 📈 성능 최적화

### 권장 설정

#### 프로덕션 환경
- **Database**: PostgreSQL 사용
- **Vector DB**: Qdrant 서버 모드
- **Cache**: Redis 클러스터
- **Load Balancer**: Nginx

#### 개발 환경
- **Database**: SQLite
- **Vector DB**: 메모리 모드
- **Cache**: 메모리 기반

## 🤝 기여 가이드

### 개발 워크플로우

1. **이슈 생성**: 기능 요청 또는 버그 리포트
2. **브랜치 생성**: `feature/기능명` 또는 `fix/버그명`
3. **개발 및 테스트**: 코드 작성 및 테스트 추가
4. **Pull Request**: 코드 리뷰 요청
5. **머지**: 승인 후 main 브랜치에 병합

### 코딩 컨벤션

- **Python**: PEP 8 준수
- **JavaScript**: ES6+ 표준
- **API**: RESTful 설계 원칙
- **문서**: Markdown 형식

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 👥 팀

- **개발팀**: 뉴스 분석 플랫폼 개발팀
- **연락처**: contact@newsanalysis.com

## 🔗 관련 링크

- [프로젝트 데모](http://localhost:5000)
- [API 문서](http://localhost:8000/docs)
- [기술 블로그](https://blog.newsanalysis.com)

---

**⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요!**