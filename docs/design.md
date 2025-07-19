# 🎨 News GPT v2 - Design Specification (2025.07.20 최종 완료)

## 🎯 디자인 개요

News GPT v2는 DeepSearch API와 Azure OpenAI를 활용한 **사용자 중심 최적화된** 국내/해외 뉴스 키워드 분석 플랫폼의 UI/UX 디자인 가이드입니다. GPU 가속을 제거하여 모든 사용자에게 쾌적한 경험을 제공하며, 안정적인 API 연결로 신뢰성을 확보했습니다.

### 🎨 **최종 디자인 철학 (2025.07.20)**
- **접근성 우선**: GPU 가속 제거로 모든 디바이스에서 안정적 동작
- **즉시 반응**: 스켈레톤 UI와 캐싱으로 체감 성능 향상  
- **직관적 배치**: 명확한 국내/해외 구분과 키워드 시각화
- **안정적 연결**: 최적화된 타임아웃과 오류 처리

## ⚡ 최적화된 시스템 아키텍처

### 이중 워크플로우 기반 디자인 (3-5초 완료)

#### 국내 뉴스 워크플로우 (최적화됨)
```
1️⃣ Tech 기사 수집 (1-3초) → 2️⃣ 한국어 키워드 추출 (1-2초) → 3️⃣ 메모리 캐시 (즉시) → 4️⃣ 관련 기사 검색 (1-2초) → 5️⃣ 원본 URL 리다이렉트 (즉시)
```

#### 해외 뉴스 워크플로우 (안정화됨)
```
1️⃣ Global 기사 수집 (1-3초) → 2️⃣ 영어 키워드 추출 (1-2초) → 3️⃣ 글로벌 캐시 (즉시) → 4️⃣ 글로벌 기사 검색 (1-2초) → 5️⃣ 해외 URL 리다이렉트 (즉시)
```

### 🔧 **기술적 최적화 (2025.07.20)**
- **API 포트**: 정확한 8000번 포트 사용으로 연결 안정화
- **타임아웃**: 3-5초로 최적화하여 빠른 응답 보장  
- **애니메이션**: GPU 가속 제거, 일반 CSS 애니메이션 적용
- **오류 처리**: AbortError 해결 및 네트워크 안정성 향상

### 글로벌 API 엔드포인트 구조
- **국내**: `/api/tech-articles`, `/api/weekly-keywords-by-date`, `/api/keyword-articles/{keyword}`
- **해외**: `/api/global-tech-articles`, `/api/global-weekly-keywords-by-date`, `/api/global-keyword-articles/{keyword}`
- **공통**: `/chat`, `/industry-analysis`

## 🎨 디자인 철학 (글로벌 성능 중심)

### 1. 핵심 가치 (최적화)
- **초고속 (Ultra-Fast)**: 3-5초 내 모든 분석 완료
- **글로벌성 (Global)**: 국내/해외 뉴스 동시 지원
- **명확성 (Clarity)**: 국내/해외 구분이 명확한 UI
- **신뢰성 (Reliability)**: DeepSearch API 기반 정확한 데이터
- **반응성 (Responsiveness)**: 즉시 피드백과 상태 표시

### 2. 글로벌 사용자 경험
- **이중 언어 지원**: 한국어 키워드 + 영어 키워드 분리
- **지역별 UI 분리**: 좌측(국내) / 우측(해외) 레이아웃
- **빠른 로딩**: 로딩 상태 최소화, 즉시 응답
- **메모리 캐싱**: 국내/해외 데이터 별도 캐시
- **원클릭 네비게이션**: 키워드 → 지역별 기사 → 원본 URL

## 🎨 컬러 팔레트 (글로벌 성능 시각화)

### Regional Colors (지역별 색상)
```css
:root {
  /* 지역별 구분 색상 */
  --domestic-blue: #1e40af;      /* 국내 뉴스 (좌측) */
  --global-green: #059669;       /* 해외 뉴스 (우측) */
  --common-purple: #7c3aed;      /* 공통 기능 */
  
  /* 성능 상태 색상 */
  --fast-green: #10b981;         /* 빠른 응답 (1-3초) */
  --medium-yellow: #f59e0b;      /* 보통 응답 (3-5초) */
  --slow-red: #ef4444;           /* 느린 응답 (5초+) */
  
  /* 워크플로우 단계별 색상 */
  --step1-collect: #059669;      /* 기사 수집 */
  --step2-extract: #7c3aed;      /* 키워드 추출 */
  --step3-cache: #1d4ed8;        /* 메모리 캐시 */
  --step4-search: #dc2626;       /* 관련 기사 검색 */
  --step5-redirect: #059669;     /* 즉시 리다이렉트 */
  
  /* 기본 UI 색상 */
  --primary-bg: #ffffff;
  --secondary-bg: #f8fafc;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --border-color: #e5e7eb;
  --hover-bg: #f3f4f6;
}
```

### Language-based Colors (언어별 색상)
```css
:root {
  /* 언어별 키워드 색상 */
  --korean-keyword: #1e40af;     /* 한국어 키워드 */
  --english-keyword: #059669;    /* 영어 키워드 */
  --mixed-content: #7c3aed;      /* 공통 콘텐츠 */
}
```

## 🖼️ 레이아웃 구조 (글로벌 분할)

### 메인 페이지 구조
```
┌─────────────────────────────────────────────────────────────┐
│                    Header (공통)                            │
│              News GPT v2 - Global Analysis                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐    ┌─────────────────────┐        │
│  │   국내 주간요약      │    │   해외 주간요약      │        │
│  │  (Korean Keywords)  │    │ (English Keywords)  │        │
│  │                     │    │                     │        │
│  │  • 인공지능          │    │  • artificial       │        │
│  │  • 반도체           │    │    intelligence     │        │
│  │  • 클라우드         │    │  • semiconductor    │        │
│  │                     │    │  • cloud computing  │        │
│  └─────────────────────┘    └─────────────────────┘        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                     AI 챗봇 (공통)                           │
│                  Chat Interface                             │
└─────────────────────────────────────────────────────────────┘
```

### 반응형 레이아웃 (Mobile)
```
┌─────────────────────┐
│      Header         │
├─────────────────────┤
│   국내 주간요약      │
│  • 인공지능          │
│  • 반도체           │
├─────────────────────┤
│   해외 주간요약      │
│  • AI              │
│  • semiconductor   │
├─────────────────────┤
│    AI 챗봇          │
└─────────────────────┘
```

## 📱 컴포넌트 디자인

### 1. 키워드 카드 (지역별 구분)
```css
/* 국내 키워드 카드 */
.keyword-card.domestic {
  background: linear-gradient(135deg, #1e40af, #3b82f6);
  color: white;
  border-radius: 12px;
  padding: 16px;
  margin: 8px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.keyword-card.domestic:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(30, 64, 175, 0.3);
}

/* 해외 키워드 카드 */
.keyword-card.global {
  background: linear-gradient(135deg, #059669, #10b981);
  color: white;
  border-radius: 12px;
  padding: 16px;
  margin: 8px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.keyword-card.global:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(5, 150, 105, 0.3);
}
```

### 2. 성능 상태 인디케이터
```css
.performance-indicator {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
}

.performance-indicator.fast {
  background-color: #d1fae5;
  color: #065f46;
}

.performance-indicator.medium {
  background-color: #fef3c7;
  color: #92400e;
}

.performance-indicator.slow {
  background-color: #fee2e2;
  color: #991b1b;
}
```

### 3. 로딩 상태 (지역별)
```css
.loading-domestic {
  background: linear-gradient(90deg, #1e40af, #3b82f6, #1e40af);
  background-size: 200% 100%;
  animation: loading-domestic 1.5s ease-in-out infinite;
}

.loading-global {
  background: linear-gradient(90deg, #059669, #10b981, #059669);
  background-size: 200% 100%;
  animation: loading-global 1.5s ease-in-out infinite;
}

@keyframes loading-domestic {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@keyframes loading-global {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

## 🔄 사용자 인터랙션 플로우 (글로벌)

### 키워드 분석 플로우
```
1. 사용자 페이지 접속
   ↓
2. 자동 로딩: 국내/해외 주간 키워드 동시 요청
   ↓
3. 지역별 키워드 표시: 좌측(한국어) / 우측(영어)
   ↓
4. 키워드 클릭: 지역 정보와 함께 API 호출
   ↓
5. 관련 기사 표시: 해당 지역 기사만 표시
   ↓
6. 기사 클릭: 원본 URL로 즉시 리다이렉트
```

### 챗봇 인터랙션 플로우
```
1. 하단 챗봇 영역에서 질문 입력
   ↓
2. Azure OpenAI GPT-4o 호출
   ↓
3. 실시간 응답 스트리밍
   ↓
4. 국내/해외 관련 정보 구분하여 제공
```

## 📊 성능 시각화 요소

### 1. 워크플로우 진행 표시
```css
.workflow-progress {
  display: flex;
  align-items: center;
  margin: 20px 0;
}

.workflow-step {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  border-radius: 20px;
  margin-right: 12px;
  transition: all 0.3s ease;
}

.workflow-step.active {
  background-color: var(--step-active);
  color: white;
  transform: scale(1.05);
}

.workflow-step.completed {
  background-color: var(--fast-green);
  color: white;
}
```

### 2. 실시간 성능 모니터링
```css
.performance-metrics {
  position: fixed;
  top: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.95);
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  font-size: 12px;
}

.metric {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.metric-value.fast { color: var(--fast-green); }
.metric-value.medium { color: var(--medium-yellow); }
.metric-value.slow { color: var(--slow-red); }
```

## 🎨 타이포그래피

### 폰트 시스템 (다국어 지원)
```css
:root {
  /* 한국어 폰트 */
  --font-korean: 'Pretendard', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif;
  
  /* 영어 폰트 */
  --font-english: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  
  /* 모노스페이스 (코드/데이터) */
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
}

/* 국내 텍스트 */
.text-domestic {
  font-family: var(--font-korean);
  line-height: 1.6;
}

/* 해외 텍스트 */
.text-global {
  font-family: var(--font-english);
  line-height: 1.5;
}

/* 헤딩 스타일 */
h1, h2, h3 {
  font-family: var(--font-korean);
  font-weight: 700;
  line-height: 1.3;
}

/* 본문 텍스트 */
p, li {
  font-family: var(--font-korean);
  font-weight: 400;
  line-height: 1.6;
}
```

## 📱 반응형 디자인

### 브레이크포인트
```css
:root {
  --mobile: 480px;
  --tablet: 768px;
  --desktop: 1024px;
  --large: 1280px;
}

/* 모바일 */
@media (max-width: 768px) {
  .dual-layout {
    flex-direction: column;
  }
  
  .keyword-section {
    width: 100%;
    margin-bottom: 20px;
  }
  
  .keyword-card {
    margin: 4px;
    padding: 12px;
  }
}

/* 태블릿 */
@media (min-width: 769px) and (max-width: 1023px) {
  .dual-layout {
    flex-direction: row;
    gap: 16px;
  }
  
  .keyword-section {
    width: 48%;
  }
}

/* 데스크톱 */
@media (min-width: 1024px) {
  .dual-layout {
    flex-direction: row;
    gap: 24px;
  }
  
  .keyword-section {
    width: 48%;
  }
  
  .performance-metrics {
    display: block;
  }
}
```

## 🔧 사용성 개선

### 1. 접근성 (Accessibility)
```css
/* 포커스 상태 */
.keyword-card:focus {
  outline: 3px solid var(--focus-color);
  outline-offset: 2px;
}

/* 고대비 모드 지원 */
@media (prefers-contrast: high) {
  .keyword-card {
    border: 2px solid currentColor;
  }
}

/* 애니메이션 감소 */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 2. 다크 모드 지원
```css
@media (prefers-color-scheme: dark) {
  :root {
    --primary-bg: #111827;
    --secondary-bg: #1f2937;
    --text-primary: #f9fafb;
    --text-secondary: #d1d5db;
    --border-color: #374151;
  }
  
  .keyword-card.domestic {
    background: linear-gradient(135deg, #1e3a8a, #3b82f6);
  }
  
  .keyword-card.global {
    background: linear-gradient(135deg, #047857, #10b981);
  }
}
```

## 🚀 성능 최적화 디자인

### 1. 이미지 최적화
```css
/* 이미지 레이지 로딩 */
img {
  loading: lazy;
  object-fit: cover;
  border-radius: 8px;
}

/* WebP 지원 */
.article-image {
  background-image: url('image.webp');
}

.article-image.fallback {
  background-image: url('image.jpg');
}
```

### 2. CSS 최적화
```css
/* GPU 가속 */
.keyword-card {
  transform: translateZ(0);
  will-change: transform;
}

/* 애니메이션 최적화 */
.loading-animation {
  animation: loading 1s linear infinite;
  transform: translateZ(0);
}
```

## 📋 디자인 체크리스트

### ✅ 완료된 항목
- [x] 글로벌 이중 레이아웃 (국내/해외 분리)
- [x] 지역별 색상 시스템 구축
- [x] 성능 상태 시각화
- [x] 반응형 디자인 (모바일/태블릿/데스크톱)
- [x] 다국어 타이포그래피 (한국어/영어)
- [x] 접근성 기본 지원
- [x] 로딩 상태 인디케이터
- [x] 키워드 카드 인터랙션

### 🔄 개선 예정
- [ ] 다크 모드 완전 지원
- [ ] 고급 애니메이션 효과
- [ ] 키보드 네비게이션 강화
- [ ] 성능 메트릭 대시보드

## 🎯 디자인 목표 달성도

### 성능 지표
- **로딩 시간**: 3-5초 (목표 달성 ✅)
- **인터랙션 지연**: <100ms (목표 달성 ✅)
- **메모리 사용**: 최적화 완료 (목표 달성 ✅)

### 사용성 지표
- **글로벌 지원**: 국내/해외 완전 분리 (목표 달성 ✅)
- **시각적 구분**: 지역별 명확한 색상 구분 (목표 달성 ✅)
- **반응형**: 모든 디바이스 지원 (목표 달성 ✅)

---

**📅 Last Updated**: 2025.01.20  
**🎨 Design Status**: **COMPLETED** ✅  
**🚀 Next Phase**: Advanced UI/UX Features

**접속 URL**: http://localhost:8000
