# 🏗️ System Design Document - NEWS GPT v2

## 📋 문서 개요

### 문서 목적
NEWS GPT v2 시스템의 전체 아키텍처, 컴포넌트 설계, 데이터 모델, API 설계 등을 상세히 기술하여 개발 및 유지보수의 가이드라인을 제공

### 문서 범위
- 시스템 아키텍처 및 컴포넌트 설계
- 데이터베이스 및 데이터 모델 설계
- API 설계 및 인터페이스 명세
- 사용자 인터페이스 설계
- 보안 및 성능 고려사항

### 대상 독자
- 백엔드 개발자
- 프론트엔드 개발자
- 시스템 아키텍트
- 데브옵스 엔지니어

## 🏛️ 시스템 아키텍처 (System Architecture)

### 전체 아키텍처 개요
```
┌─────────────────────────────────────────────────────────────────┐
│                        NEWS GPT v2 Architecture                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  │   Frontend      │    │   Backend       │    │  External APIs  │
│  │                 │    │                 │    │                 │
│  │  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │  │ HTML/CSS  │  │    │  │ FastAPI   │  │    │  │ Azure     │  │
│  │  │ JavaScript│  │◄──►│  │ Server    │  │◄──►│  │ OpenAI    │  │
│  │  │ React     │  │    │  │ (Port     │  │    │  │           │  │
│  │  │ (Future)  │  │    │  │ 8000)     │  │    │  │           │  │
│  │  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
│  │                 │    │                 │    │                 │
│  │  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │  │ Chat UI   │  │    │  │ Business  │  │    │  │ Azure     │  │
│  │  │ Dashboard │  │    │  │ Logic     │  │    │  │ AI Search │  │
│  │  │ Analytics │  │    │  │ Layer     │  │    │  │           │  │
│  │  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
│  │                 │    │                 │    │                 │
│  └─────────────────┘    │  ┌───────────┐  │    │  ┌───────────┐  │
│                         │  │ Data      │  │    │  │ Naver     │  │
│  ┌─────────────────┐    │  │ Processing│  │    │  │ News API  │  │
│  │   Data Scripts  │    │  │ Scripts   │  │    │  │           │  │
│  │                 │    │  └───────────┘  │    │  └───────────┘  │
│  │ run_analysis.py │    │                 │    │                 │
│  │ upload_*.py     │    │                 │    │                 │
│  │ check_*.py      │    │                 │    │                 │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 아키텍처 패턴
- **패턴**: 3-Tier Architecture (Presentation, Business, Data)
- **통신 방식**: RESTful API, JSON over HTTP
- **배포 방식**: 로컬 개발 → 컨테이너 기반 클라우드 배포

### 주요 설계 원칙
1. **관심사 분리**: 각 계층별 명확한 역할 분담
2. **느슨한 결합**: 컴포넌트 간 의존성 최소화
3. **확장성**: 모듈 단위 수평 확장 가능
4. **재사용성**: 공통 모듈 및 유틸리티 분리
5. **보안**: 환경변수 기반 설정, HTTPS 통신

## 🔧 컴포넌트 설계 (Component Design)

### 1. Frontend Layer

#### 1.1 Web Application (`index.html`)
```
Web Application
├── Layout Components
│   ├── Header (타이틀, 네비게이션)
│   ├── Main Content Area
│   └── Footer
├── Feature Components
│   ├── Weekly Summary Section
│   ├── Keywords Dashboard
│   ├── Chat Interface
│   ├── Industry Analysis Tabs
│   └── Article List
└── Utilities
    ├── API Client
    ├── State Management
    └── UI Helpers
```

**기술 스택**:
- HTML5, CSS3, JavaScript ES6+
- Inter 폰트 (Google Fonts)
- Fetch API for HTTP requests
- CSS Grid/Flexbox for layouts

#### 1.2 Chat Interface
```javascript
// 채팅 인터페이스 컴포넌트 구조
ChatInterface = {
  elements: {
    inputField: '#chat-input',
    sendButton: '#send-btn',
    messagesContainer: '#messages',
    typingIndicator: '#typing'
  },
  
  methods: {
    sendMessage(),
    displayMessage(),
    showTyping(),
    scrollToBottom()
  }
}
```

### 2. Backend Layer

#### 2.1 FastAPI Application (`main.py`)
```python
# FastAPI 애플리케이션 구조
app = FastAPI(
    title="NEWS GPT v2 API",
    description="AI 뉴스 키워드 분석 플랫폼",
    version="2.0.0"
)

# 미들웨어 구성
app.add_middleware(CORSMiddleware)
app.add_middleware(GZipMiddleware)
app.add_middleware(TrustedHostMiddleware)

# 라우터 구성
app.include_router(news_router, prefix="/api/news")
app.include_router(chat_router, prefix="/api/chat")
app.include_router(analysis_router, prefix="/api/analysis")
```

#### 2.2 Service Layer
```python
# 서비스 레이어 구조
services/
├── news_service.py          # 뉴스 관련 비즈니스 로직
├── keyword_service.py       # 키워드 분석 서비스
├── chat_service.py          # 챗봇 서비스
├── search_service.py        # 검색 서비스
└── analysis_service.py      # 분석 서비스
```

#### 2.3 Data Access Layer
```python
# 데이터 접근 레이어
repositories/
├── azure_search_repository.py    # Azure AI Search 연동
├── openai_repository.py          # Azure OpenAI 연동
├── naver_repository.py           # 네이버 API 연동
└── cache_repository.py           # 캐시 처리
```

### 3. Data Processing Layer

#### 3.1 News Collection (`run_analysis.py`)
```python
# 뉴스 수집 파이프라인
NewsCollectionPipeline = {
    'stages': [
        'keyword_search',      # 키워드 기반 검색
        'data_extraction',     # 데이터 추출
        'deduplication',       # 중복 제거
        'text_preprocessing',  # 텍스트 전처리
        'keyword_extraction',  # 키워드 추출
        'analysis_generation', # 분석 생성
        'data_upload'         # 데이터 업로드
    ]
}
```

#### 3.2 Keyword Analysis Engine
```python
# 키워드 분석 엔진
class KeywordAnalyzer:
    def __init__(self):
        self.openai_client = AzureOpenAI()
        self.search_client = SearchClient()
    
    def extract_keywords(self, text: str) -> List[str]:
        """GPT-4o를 사용한 키워드 추출"""
        pass
    
    def analyze_frequency(self, keywords: List[str]) -> Dict:
        """키워드 빈도 분석"""
        pass
    
    def generate_weekly_summary(self, keywords: Dict) -> str:
        """주간 요약 생성"""
        pass
```

## 🗄️ 데이터 모델 설계 (Data Model Design)

### 1. Azure AI Search Index Schema

#### 1.1 News Article Schema
```json
{
  "name": "news_index",
  "fields": [
    {
      "name": "id",
      "type": "Edm.String",
      "key": true,
      "searchable": false,
      "filterable": true
    },
    {
      "name": "title",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "sortable": false
    },
    {
      "name": "content",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "sortable": false
    },
    {
      "name": "date",
      "type": "Edm.String",
      "searchable": false,
      "filterable": true,
      "sortable": true
    },
    {
      "name": "section",
      "type": "Edm.String",
      "searchable": false,
      "filterable": true,
      "sortable": false
    },
    {
      "name": "keyword",
      "type": "Edm.String",
      "searchable": true,
      "filterable": true,
      "sortable": false
    },
    {
      "name": "embedding",
      "type": "Collection(Edm.Single)",
      "searchable": true,
      "retrievable": false,
      "dimensions": 1536,
      "vectorSearchProfile": "vector-profile"
    }
  ],
  "vectorSearch": {
    "profiles": [
      {
        "name": "vector-profile",
        "algorithm": "hnsw"
      }
    ]
  }
}
```

#### 1.2 Weekly Summary Schema
```json
{
  "name": "weekly_summary",
  "fields": [
    {
      "name": "id",
      "type": "Edm.String",
      "key": true
    },
    {
      "name": "title",
      "type": "Edm.String",
      "searchable": true
    },
    {
      "name": "content",
      "type": "Edm.String",
      "searchable": true
    },
    {
      "name": "date",
      "type": "Edm.String",
      "filterable": true
    },
    {
      "name": "top_keywords",
      "type": "Collection(Edm.String)",
      "searchable": true,
      "filterable": true
    },
    {
      "name": "statistics",
      "type": "Edm.String",
      "searchable": false
    }
  ]
}
```

### 2. Data Transfer Objects (DTOs)

#### 2.1 News Article DTO
```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class NewsArticleDTO(BaseModel):
    id: str
    title: str
    content: str
    date: str
    section: str
    keyword: str
    url: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

#### 2.2 Keyword Analysis DTO
```python
class KeywordAnalysisDTO(BaseModel):
    keyword: str
    frequency: int
    rank: int
    trend: str  # 'up', 'down', 'stable'
    related_articles: List[str]
    sentiment_score: Optional[float] = None
```

#### 2.3 Chat Message DTO
```python
class ChatMessageDTO(BaseModel):
    message: str
    timestamp: datetime
    response_time: Optional[float] = None
    
class ChatResponseDTO(BaseModel):
    answer: str
    sources: List[str]
    confidence: float
    keywords: List[str]
```

### 3. Domain Models

#### 3.1 News Domain Model
```python
class NewsArticle:
    def __init__(self, title: str, content: str, date: str):
        self.title = title
        self.content = content
        self.date = date
        self.keywords = []
        self.sentiment = None
    
    def extract_keywords(self) -> List[str]:
        """키워드 추출 메서드"""
        pass
    
    def analyze_sentiment(self) -> float:
        """감정 분석 메서드"""
        pass
```

#### 3.2 Keyword Domain Model
```python
class Keyword:
    def __init__(self, text: str, frequency: int = 0):
        self.text = text
        self.frequency = frequency
        self.related_articles = []
        self.trend = 'stable'
    
    def calculate_trend(self, previous_frequency: int) -> str:
        """트렌드 계산 메서드"""
        pass
```

## 🔌 API 설계 (API Design)

### 1. RESTful API 구조

#### 1.1 Base URL
```
Development: http://localhost:8000
Production: https://news-gpt-v2.azurewebsites.net (예정)
```

#### 1.2 API 엔드포인트 설계

##### News API
```yaml
/api/news:
  get:
    summary: 뉴스 목록 조회
    parameters:
      - name: keyword
        in: query
        schema:
          type: string
      - name: limit
        in: query
        schema:
          type: integer
          default: 10
    responses:
      200:
        description: 뉴스 목록
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/NewsArticle'
```

##### Keywords API
```yaml
/api/keywords:
  get:
    summary: 키워드 목록 조회
    responses:
      200:
        description: 키워드 목록
        content:
          application/json:
            schema:
              type: object
              properties:
                keywords:
                  type: array
                  items:
                    type: string
                week_info:
                  type: string

/api/keywords/{keyword}/articles:
  get:
    summary: 키워드 관련 기사 조회
    parameters:
      - name: keyword
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: 관련 기사 목록
```

##### Chat API
```yaml
/api/chat:
  post:
    summary: 챗봇 대화
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              message:
                type: string
            required:
              - message
    responses:
      200:
        description: 챗봇 응답
        content:
          application/json:
            schema:
              type: object
              properties:
                answer:
                  type: string
                sources:
                  type: array
                  items:
                    type: string
                confidence:
                  type: number
```

##### Analysis API
```yaml
/api/analysis/weekly-summary:
  get:
    summary: 주간 요약 조회
    responses:
      200:
        description: 주간 요약
        content:
          application/json:
            schema:
              type: object
              properties:
                title:
                  type: string
                content:
                  type: string
                top_keywords:
                  type: array
                  items:
                    type: string

/api/analysis/section/{section}:
  get:
    summary: 섹션별 분석 조회
    parameters:
      - name: section
        in: path
        required: true
        schema:
          type: string
          enum: [사회, 경제, IT과학, 세계, 생활문화]
    responses:
      200:
        description: 섹션별 분석 결과
```

### 2. WebSocket API (향후 구현 예정)

#### 2.1 실시간 업데이트
```yaml
/ws/updates:
  description: 실시간 키워드 업데이트
  events:
    - keyword_update
    - news_added
    - analysis_complete
```

#### 2.2 실시간 채팅
```yaml
/ws/chat:
  description: 실시간 챗봇 대화
  events:
    - message_sent
    - typing_indicator
    - message_received
```

### 3. API 응답 표준화

#### 3.1 성공 응답 구조
```json
{
  "status": "success",
  "data": {
    // 실제 데이터
  },
  "meta": {
    "timestamp": "2025-07-18T10:00:00Z",
    "version": "2.0.0"
  }
}
```

#### 3.2 에러 응답 구조
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_REQUEST",
    "message": "요청 파라미터가 올바르지 않습니다.",
    "details": {
      "field": "keyword",
      "reason": "키워드는 필수 입력값입니다."
    }
  },
  "meta": {
    "timestamp": "2025-07-18T10:00:00Z",
    "version": "2.0.0"
  }
}
```

## 🎨 사용자 인터페이스 설계 (UI Design)

### 1. 전체 레이아웃 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                         Header                                  │
│  🔍 AI 뉴스 키워드 분석    [주간 키워드] [채팅] [분석] [설정]     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐  │
│  │   주간 요약 섹션     │    │        채팅 인터페이스           │  │
│  │                     │    │                                 │  │
│  │  📊 TOP 3 키워드    │    │  ┌─────────────────────────────┐  │  │
│  │  [인공지능] [반도체] │    │  │      메시지 히스토리        │  │  │
│  │  [AI]               │    │  │                             │  │  │
│  │                     │    │  └─────────────────────────────┘  │  │
│  │  📈 트렌드 차트     │    │                                 │  │
│  │                     │    │  ┌─────────────────────────────┐  │  │
│  └─────────────────────┘    │  │      입력 필드              │  │  │
│                              │  │  메시지 입력... [전송]      │  │  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                   산업별 분석 탭                            │  │
│  │  [사회] [경제] [IT과학] [세계] [생활문화]                   │  │
│  │                                                             │  │
│  │  현재 선택: 경제 관점                                       │  │
│  │  💰 경제적 파급효과, 시장 규모, 투자 동향...               │  │
│  │                                                             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                   관련 기사 목록                            │  │
│  │  📄 기사 제목 1 - 2025.07.18                              │  │
│  │  📄 기사 제목 2 - 2025.07.17                              │  │
│  │  📄 기사 제목 3 - 2025.07.16                              │  │
│  │                                                             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 컴포넌트 설계

#### 2.1 Header Component
```css
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header h1 {
  font-family: 'Inter', sans-serif;
  font-weight: 300;
  font-size: 2.5rem;
}

.nav-tabs {
  display: flex;
  gap: 20px;
}

.nav-tab {
  padding: 10px 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
}

.nav-tab:hover {
  background: rgba(255, 255, 255, 0.2);
}
```

#### 2.2 Weekly Summary Component
```css
.weekly-summary {
  background: white;
  border-radius: 16px;
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.keywords-container {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 20px;
}

.keyword-tag {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.keyword-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}
```

#### 2.3 Chat Interface Component
```css
.chat-container {
  background: white;
  border-radius: 16px;
  padding: 20px;
  height: 400px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 10px;
}

.message {
  padding: 10px;
  margin: 5px 0;
  border-radius: 8px;
  max-width: 80%;
}

.message.user {
  background: #667eea;
  color: white;
  align-self: flex-end;
  margin-left: auto;
}

.message.bot {
  background: #f5f5f5;
  color: #333;
  align-self: flex-start;
}

.chat-input-container {
  display: flex;
  gap: 10px;
}

.chat-input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  font-family: 'Inter', sans-serif;
}

.send-button {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.send-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}
```

### 3. 반응형 디자인

#### 3.1 브레이크포인트
```css
/* 모바일 퍼스트 접근 */
:root {
  --mobile: 320px;
  --tablet: 768px;
  --desktop: 1024px;
  --wide: 1440px;
}

/* 모바일 (기본) */
.main-container {
  max-width: 100%;
  padding: 0 16px;
}

/* 태블릿 */
@media (min-width: 768px) {
  .main-container {
    max-width: 768px;
    margin: 0 auto;
    padding: 0 24px;
  }
  
  .grid-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }
}

/* 데스크톱 */
@media (min-width: 1024px) {
  .main-container {
    max-width: 1200px;
    padding: 0 32px;
  }
  
  .grid-container {
    grid-template-columns: 2fr 1fr;
    gap: 32px;
  }
}
```

#### 3.2 모바일 최적화
```css
/* 모바일 네비게이션 */
@media (max-width: 767px) {
  .nav-tabs {
    flex-direction: column;
    gap: 8px;
  }
  
  .nav-tab {
    padding: 8px 16px;
    font-size: 14px;
  }
  
  .chat-container {
    height: 300px;
  }
  
  .keywords-container {
    flex-direction: column;
    gap: 8px;
  }
  
  .keyword-tag {
    text-align: center;
    padding: 10px;
  }
}
```

## 🔐 보안 설계 (Security Design)

### 1. 인증 및 인가

#### 1.1 API 키 관리
```python
# 환경변수 기반 API 키 관리
import os
from functools import wraps

class APIKeyManager:
    def __init__(self):
        self.keys = {
            'azure_openai': os.getenv('AZURE_OPENAI_API_KEY'),
            'azure_search': os.getenv('AZURE_SEARCH_API_KEY'),
            'naver_news': os.getenv('NAVER_CLIENT_ID')
        }
    
    def validate_key(self, service: str) -> bool:
        return bool(self.keys.get(service))
    
    def get_key(self, service: str) -> str:
        if not self.validate_key(service):
            raise ValueError(f"Missing API key for {service}")
        return self.keys[service]

# API 키 검증 데코레이터
def require_api_key(service: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_manager = APIKeyManager()
            if not key_manager.validate_key(service):
                raise HTTPException(
                    status_code=401,
                    detail=f"Invalid or missing API key for {service}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

#### 1.2 Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat")
@limiter.limit("10/minute")  # 분당 10회 제한
async def chat_endpoint(request: Request, query: ChatQuery):
    # 채팅 로직
    pass

@app.get("/api/news")
@limiter.limit("100/hour")  # 시간당 100회 제한
async def get_news(request: Request):
    # 뉴스 조회 로직
    pass
```

### 2. 데이터 보호

#### 2.1 입력 검증
```python
from pydantic import BaseModel, validator
import re

class ChatQuery(BaseModel):
    message: str
    
    @validator('message')
    def validate_message(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('메시지는 필수입니다.')
        if len(v) > 1000:
            raise ValueError('메시지는 1000자를 초과할 수 없습니다.')
        # XSS 방지를 위한 HTML 태그 제거
        clean_message = re.sub('<[^<]+?>', '', v)
        return clean_message.strip()

class KeywordQuery(BaseModel):
    keyword: str
    
    @validator('keyword')
    def validate_keyword(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('키워드는 필수입니다.')
        # SQL 인젝션 방지
        if re.search(r'[;\'"\\]', v):
            raise ValueError('허용되지 않는 문자가 포함되어 있습니다.')
        return v.strip()
```

#### 2.2 출력 새니타이징
```python
import html

def sanitize_output(text: str) -> str:
    """HTML 엔티티 인코딩"""
    return html.escape(text)

def filter_sensitive_data(data: dict) -> dict:
    """민감 데이터 필터링"""
    sensitive_keys = ['api_key', 'secret', 'password', 'token']
    filtered_data = {}
    
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            filtered_data[key] = '*' * 8
        else:
            filtered_data[key] = value
    
    return filtered_data
```

### 3. 통신 보안

#### 3.1 HTTPS 강제
```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# 프로덕션 환경에서만 HTTPS 강제
if os.getenv('ENVIRONMENT') == 'production':
    app.add_middleware(HTTPSRedirectMiddleware)
```

#### 3.2 CORS 설정
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 프로덕션에서는 특정 도메인만
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## ⚡ 성능 설계 (Performance Design)

### 1. 캐싱 전략

#### 1.1 메모리 캐싱
```python
from functools import lru_cache
import asyncio
from typing import Dict, Any

class MemoryCache:
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Any:
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        if len(self.cache) >= self.max_size:
            # LRU 정책으로 가장 오래된 항목 제거
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl
        }
    
    def is_expired(self, key: str) -> bool:
        if key not in self.cache:
            return True
        return time.time() > self.cache[key]['expires_at']

# 캐시 인스턴스
cache = MemoryCache()

@lru_cache(maxsize=100)
def get_weekly_keywords() -> List[str]:
    """주간 키워드 캐싱"""
    # 실제 데이터 조회 로직
    pass
```

#### 1.2 HTTP 캐싱
```python
from fastapi import Response
from fastapi.responses import JSONResponse

@app.get("/api/keywords")
async def get_keywords(response: Response):
    # 캐시 헤더 설정 (5분 캐싱)
    response.headers["Cache-Control"] = "public, max-age=300"
    response.headers["ETag"] = "weekly-keywords-v1"
    
    keywords = get_weekly_keywords()
    return JSONResponse(content={"keywords": keywords})
```

### 2. 데이터베이스 최적화

#### 2.1 인덱스 설계
```python
# Azure AI Search 인덱스 최적화
index_definition = {
    "name": "news_index",
    "fields": [
        # 검색 최적화를 위한 필드 설정
        {"name": "id", "type": "Edm.String", "key": True},
        {"name": "title", "type": "Edm.String", "searchable": True},
        {"name": "content", "type": "Edm.String", "searchable": True},
        {"name": "date", "type": "Edm.String", "filterable": True, "sortable": True},
        {"name": "keyword", "type": "Edm.String", "filterable": True}
    ],
    "scoringProfiles": [
        {
            "name": "relevance",
            "text": {
                "weights": {
                    "title": 3,
                    "content": 1
                }
            }
        }
    ]
}
```

#### 2.2 쿼리 최적화
```python
async def search_news_optimized(keyword: str, limit: int = 10) -> List[Dict]:
    """최적화된 뉴스 검색"""
    
    # 캐시 확인
    cache_key = f"search:{keyword}:{limit}"
    cached_result = cache.get(cache_key)
    
    if cached_result and not cache.is_expired(cache_key):
        return cached_result['value']
    
    # 최적화된 검색 쿼리
    search_results = await search_client.search(
        search_text=keyword,
        top=limit,
        include_total_count=True,
        scoring_profile="relevance",
        search_fields=["title", "content"],
        select=["id", "title", "content", "date"]  # 필요한 필드만 선택
    )
    
    results = [doc async for doc in search_results]
    
    # 결과 캐싱
    cache.set(cache_key, results, ttl=300)  # 5분 캐싱
    
    return results
```

### 3. 비동기 처리

#### 3.1 비동기 API 엔드포인트
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 스레드 풀 설정
executor = ThreadPoolExecutor(max_workers=4)

@app.post("/api/chat")
async def chat_async(query: ChatQuery):
    """비동기 채팅 처리"""
    
    # CPU 집약적 작업을 별도 스레드에서 처리
    loop = asyncio.get_event_loop()
    
    # 병렬 처리
    embedding_task = loop.run_in_executor(
        executor, get_embedding, query.message
    )
    
    search_task = loop.run_in_executor(
        executor, search_similar_content, query.message
    )
    
    # 결과 대기
    embedding, search_results = await asyncio.gather(
        embedding_task, search_task
    )
    
    # 답변 생성
    answer = await generate_answer_async(query.message, search_results)
    
    return {"answer": answer, "sources": search_results}
```

#### 3.2 백그라운드 작업
```python
from fastapi import BackgroundTasks

@app.post("/api/news/collect")
async def trigger_news_collection(background_tasks: BackgroundTasks):
    """뉴스 수집 백그라운드 작업"""
    
    background_tasks.add_task(collect_and_process_news)
    
    return {"message": "뉴스 수집이 시작되었습니다."}

async def collect_and_process_news():
    """백그라운드 뉴스 수집 및 처리"""
    try:
        # 뉴스 수집
        news_data = await collect_news_async()
        
        # 키워드 추출
        keywords = await extract_keywords_batch(news_data)
        
        # 데이터 업로드
        await upload_to_search_index(news_data, keywords)
        
        # 캐시 무효화
        cache.clear_pattern("search:*")
        cache.clear_pattern("keywords:*")
        
    except Exception as e:
        logger.error(f"뉴스 수집 오류: {e}")
```

## 📊 모니터링 및 로깅 (Monitoring & Logging)

### 1. 구조화된 로깅

#### 1.1 로깅 설정
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
            
        return json.dumps(log_obj)

# 로거 설정
logger = logging.getLogger('news_gpt_v2')
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

#### 1.2 로깅 미들웨어
```python
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # 요청 로그
        logger.info(
            f"Request started: {request.method} {request.url}",
            extra={
                'request_id': request_id,
                'method': request.method,
                'url': str(request.url),
                'client_ip': request.client.host
            }
        )
        
        try:
            response = await call_next(request)
            
            # 응답 로그
            process_time = time.time() - start_time
            logger.info(
                f"Request completed: {response.status_code}",
                extra={
                    'request_id': request_id,
                    'status_code': response.status_code,
                    'process_time': process_time
                }
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    'request_id': request_id,
                    'error': str(e),
                    'process_time': process_time
                }
            )
            raise

app.add_middleware(LoggingMiddleware)
```

### 2. 성능 모니터링

#### 2.1 메트릭 수집
```python
from prometheus_client import Counter, Histogram, Gauge
import time

# 메트릭 정의
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
active_connections = Gauge('active_connections', 'Active connections')

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # 메트릭 업데이트
            request_count.labels(
                method=request.method,
                endpoint=request.url.path
            ).inc()
            
            request_duration.observe(time.time() - start_time)
            
            return response
            
        except Exception as e:
            request_count.labels(
                method=request.method,
                endpoint=request.url.path
            ).inc()
            raise

app.add_middleware(MetricsMiddleware)
```

#### 2.2 헬스체크
```python
from sqlalchemy import text

@app.get("/health")
async def health_check():
    """시스템 헬스체크"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {}
    }
    
    # Azure OpenAI 연결 확인
    try:
        # 간단한 요청으로 연결 확인
        test_response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        health_status['services']['azure_openai'] = 'healthy'
    except Exception as e:
        health_status['services']['azure_openai'] = 'unhealthy'
        health_status['status'] = 'degraded'
    
    # Azure AI Search 연결 확인
    try:
        # 간단한 검색으로 연결 확인
        search_results = await search_client.search("test", top=1)
        health_status['services']['azure_search'] = 'healthy'
    except Exception as e:
        health_status['services']['azure_search'] = 'unhealthy'
        health_status['status'] = 'degraded'
    
    return health_status
```

## 🚀 배포 설계 (Deployment Design)

### 1. 컨테이너화

#### 1.1 Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 비루트 사용자 생성
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 애플리케이션 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 1.2 Docker Compose
```yaml
version: '3.8'

services:
  news-gpt-v2:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - news-gpt-v2
    restart: unless-stopped

volumes:
  redis_data:
```

### 2. CI/CD 파이프라인

#### 2.1 GitHub Actions
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v
    
    - name: Run linting
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
  
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t news-gpt-v2:${{ github.sha }} .
        docker tag news-gpt-v2:${{ github.sha }} news-gpt-v2:latest
    
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push news-gpt-v2:${{ github.sha }}
        docker push news-gpt-v2:latest
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to Azure
      run: |
        # Azure 배포 스크립트
        az container restart --name news-gpt-v2 --resource-group news-gpt-rg
```

### 3. 환경별 설정

#### 3.1 개발 환경
```python
# config/development.py
class DevelopmentConfig:
    DEBUG = True
    TESTING = False
    
    # 로컬 Azure 에뮬레이터 사용
    AZURE_STORAGE_CONNECTION_STRING = "UseDevelopmentStorage=true"
    
    # 개발용 API 키
    AZURE_OPENAI_API_KEY = os.getenv('DEV_AZURE_OPENAI_API_KEY')
    
    # 로깅 설정
    LOG_LEVEL = 'DEBUG'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

#### 3.2 프로덕션 환경
```python
# config/production.py
class ProductionConfig:
    DEBUG = False
    TESTING = False
    
    # 프로덕션 Azure 서비스
    AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
    AZURE_SEARCH_API_KEY = os.getenv('AZURE_SEARCH_API_KEY')
    
    # 보안 설정
    CORS_ORIGINS = ['https://yourdomain.com']
    HTTPS_REDIRECT = True
    
    # 로깅 설정
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = 'json'
```

---

📅 **작성일**: 2025년 7월 18일  
👤 **작성자**: NEWS GPT v2 개발팀  
📧 **문의**: GitHub Issues  
🔗 **관련 문서**: README.md, requirements.md, task.md  
📄 **버전**: 2.0.0
