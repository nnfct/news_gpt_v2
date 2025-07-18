# 📋 Task Management - NEWS GPT v2

## 🎯 프로젝트 개요

Azure OpenAI와 Azure AI Search를 활용한 실시간 뉴스 키워드 분석 및 트렌드 분석 플랫폼 개발

### 프로젝트 목표
- 네이버 뉴스 API를 통한 실시간 뉴스 수집
- Azure OpenAI GPT-4o를 활용한 키워드 분석
- Azure AI Search 기반 벡터 검색 구현
- 웹 기반 AI 챗봇 인터페이스 제공

## ✅ 완료된 작업 (Completed Tasks)

### Phase 1: 환경 설정 및 기본 인프라
- [x] Python 가상환경 구성 (Python 3.11.9)
- [x] 패키지 의존성 설치 (FastAPI, Uvicorn, OpenAI, Azure SDK 등)
- [x] .env 환경변수 설정 파일 구성
- [x] Azure OpenAI Service 연동
- [x] Azure AI Search 연동
- [x] 네이버 뉴스 API 연동

### Phase 2: 데이터 처리 및 분석 시스템
- [x] 뉴스 수집 스크립트 구현 (`run_analysis.py`)
- [x] 29개 IT/기술 키워드 기반 뉴스 자동 수집
- [x] Azure OpenAI GPT-4o 키워드 추출 기능
- [x] 중복 제거 및 데이터 정제 로직
- [x] Azure AI Search 인덱스 설계 및 구현
- [x] 배치 업로드 시스템 구현

### Phase 3: API 서버 개발
- [x] FastAPI 메인 서버 구현 (`main.py`)
- [x] RESTful API 엔드포인트 설계
  - [x] `/` - 메인 웹 페이지
  - [x] `/weekly-summary` - 주간 요약 조회
  - [x] `/weekly-keywords` - 주간 키워드 조회
  - [x] `/section-analysis/{section}` - 섹션별 분석
  - [x] `/chat` - AI 챗봇 대화
  - [x] `/industry-analysis` - 산업별 분석
  - [x] `/keyword-articles` - 키워드별 기사 조회
- [x] CORS 미들웨어 설정
- [x] 정적 파일 서빙 구성

### Phase 4: 웹 인터페이스 개발
- [x] 반응형 웹 디자인 구현 (`index.html`)
- [x] Inter 폰트 적용
- [x] 주간 키워드 시각화
- [x] 실시간 챗봇 인터페이스
- [x] 산업별 분석 탭 시스템
- [x] 키워드 태그 인터랙션

### Phase 5: 운영 및 배포 스크립트
- [x] Windows 배치 파일 (`start_server.bat`)
- [x] PowerShell 스크립트 (`start_server.ps1`)
- [x] 테스트 데이터 업로드 스크립트
- [x] 인덱스 상태 확인 스크립트
- [x] 데이터 검증 스크립트

## 🔄 진행 중인 작업 (In Progress)

### 최적화 및 개선
- [ ] API 요청 제한 최적화 (네이버 API 429 에러 해결)
- [ ] Azure OpenAI 콘텐츠 필터링 정책 대응
- [ ] 한글 인코딩 문제 해결
- [ ] 메모리 사용량 최적화

## 📅 향후 계획 (Future Tasks)

### Phase 6: 성능 최적화
- [ ] **캐싱 시스템 구현**
  - 자주 요청되는 키워드 결과 메모리 캐시
  - Redis 기반 세션 관리 (선택사항)
- [ ] **비동기 처리 개선**
  - FastAPI 비동기 엔드포인트 확장
  - 배경 작업 큐 시스템 구현
- [ ] **데이터베이스 최적화**
  - Azure AI Search 인덱스 성능 튜닝
  - 벡터 검색 정확도 개선

### Phase 7: 기능 확장
- [ ] **실시간 모니터링**
  - 뉴스 수집 스케줄러 구현
  - 키워드 트렌드 실시간 업데이트
  - 시스템 상태 모니터링 대시보드
- [ ] **고급 분석 기능**
  - 감정 분석 (Sentiment Analysis)
  - 키워드 연관성 분석
  - 시계열 트렌드 예측
- [ ] **사용자 경험 개선**
  - 개인화 키워드 추천
  - 북마크 및 즐겨찾기 기능
  - 분석 결과 내보내기 (PDF, Excel)

### Phase 8: 보안 및 운영
- [ ] **보안 강화**
  - Azure Key Vault 연동
  - API 키 로테이션 자동화
  - CORS 정책 세분화
- [ ] **로깅 및 모니터링**
  - 구조화된 로깅 시스템
  - 에러 추적 및 알림
  - 성능 메트릭 수집

### Phase 9: 배포 및 확장
- [ ] **컨테이너화**
  - Docker 이미지 구성
  - Docker Compose 설정
- [ ] **클라우드 배포**
  - Azure Container Instances 배포
  - Azure App Service 배포 (선택사항)
- [ ] **CI/CD 파이프라인**
  - GitHub Actions 워크플로우
  - 자동 테스트 및 배포

## 🐛 알려진 이슈 (Known Issues)

### 우선순위 HIGH
1. **네이버 API 요청 제한 (429 에러)**
   - 증상: 일부 키워드 검색 시 Too Many Requests 에러
   - 해결방안: 요청 간격 조정 (현재 0.1초 → 0.5초)
   - 담당: Backend Team

2. **Azure OpenAI 콘텐츠 필터링**
   - 증상: 일부 뉴스 콘텐츠 처리 시 content_filter 에러
   - 해결방안: 프롬프트 최적화 및 전처리 강화
   - 담당: AI/ML Team

### 우선순위 MEDIUM
3. **한글 인코딩 문제**
   - 증상: 챗봇 응답 시 한글 깨짐 현상
   - 해결방안: UTF-8 인코딩 명시적 설정
   - 담당: Frontend Team

4. **Azure AI Search 스키마 불일치**
   - 증상: url 필드 관련 업로드 오류
   - 해결방안: 스키마 정의 표준화 (완료)
   - 상태: ✅ 해결됨

## 📊 성과 지표 (KPIs)

### 데이터 수집
- ✅ **뉴스 수집량**: 161개 (목표: 100개 이상)
- ✅ **키워드 다양성**: 29개 IT/기술 키워드
- ✅ **데이터 정확도**: 중복 제거 후 품질 관리

### 시스템 성능
- ✅ **API 응답시간**: < 2초 (주간 키워드 조회)
- ✅ **서버 가용성**: 99.9% (로컬 환경)
- ⏳ **동시 사용자**: 테스트 필요

### 사용자 경험
- ✅ **웹 페이지 로딩**: < 3초
- ✅ **챗봇 응답**: < 5초
- ✅ **모바일 호환성**: 반응형 디자인 적용

## 🔧 개발 도구 및 환경

### 개발 환경
- **Python**: 3.11.9
- **가상환경**: venv
- **IDE**: VS Code
- **OS**: Windows 11

### 주요 라이브러리
- **FastAPI**: 0.116.1 (웹 프레임워크)
- **Uvicorn**: 0.35.0 (ASGI 서버)
- **OpenAI**: 1.97.0 (Azure OpenAI SDK)
- **Azure Search Documents**: 11.5.3
- **Pandas**: 2.3.1 (데이터 처리)

### 클라우드 서비스
- **Azure OpenAI**: GPT-4o 모델
- **Azure AI Search**: 벡터 검색 인덱스
- **Naver News API**: 뉴스 데이터 소스

## 🚀 배포 가이드

### 로컬 개발 환경
```bash
# 1. 저장소 클론
git clone https://github.com/nnfct/news_gpt_v2.git
cd news_gpt_v2

# 2. 가상환경 설정
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
# .env 파일 수정

# 5. 서버 실행
python main.py
```

### 프로덕션 배포 (예정)
```bash
# Docker 빌드
docker build -t news-gpt-v2 .

# 컨테이너 실행
docker run -p 8000:8000 news-gpt-v2
```

## 📝 문서화

### 완료된 문서
- [x] README.md - 프로젝트 개요 및 설치 가이드
- [x] PROJECT_REPORT.md - 프로젝트 완료 보고서
- [x] task.md - 작업 관리 및 진행 상황 (이 문서)

### 작성 예정 문서
- [ ] requirements.md - 요구사항 명세서
- [ ] design.md - 시스템 설계 문서
- [ ] API_REFERENCE.md - API 상세 문서
- [ ] DEPLOYMENT_GUIDE.md - 배포 가이드

## 🤝 팀 구성 및 역할

### Backend Developer
- FastAPI 서버 개발 및 유지보수
- Azure 서비스 연동 및 최적화
- 데이터 파이프라인 구현

### AI/ML Engineer
- Azure OpenAI 모델 최적화
- 키워드 추출 알고리즘 개선
- 벡터 검색 정확도 향상

### Frontend Developer
- 웹 인터페이스 개발
- 사용자 경험 최적화
- 반응형 디자인 구현

### DevOps Engineer
- CI/CD 파이프라인 구축
- 컨테이너화 및 배포 자동화
- 모니터링 시스템 구성

---

📅 **마지막 업데이트**: 2025년 7월 18일  
📧 **프로젝트 문의**: GitHub Issues  
🔗 **저장소**: https://github.com/nnfct/news_gpt_v2