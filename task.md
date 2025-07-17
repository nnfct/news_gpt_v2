Implementation Plan (Hybrid: Azure AI + Local Execution)
1. 개발 환경 및 Azure 서비스 준비
1.1 Python 가상 환경 설정 (venv)
requirements.txt에 필요한 라이브러리 명시 (FastAPI, Uvicorn, OpenAI, Azure AI Search SDK, Pandas)
1.2 핵심 Azure 서비스 생성
Azure OpenAI Service: GPT-4o, text-embedding-3-large 모델 배포
Azure AI Search: 벡터 검색을 위한 인덱스 생성
1.3 접속 정보 설정
.env 파일에 생성한 Azure 서비스들의 API 키, 엔드포인트 정보를 안전하게 관리
2. 데이터 저장소 설계 (Azure AI Search)
2.1 Azure AI Search 인덱스 설계
분석 카드 데이터를 저장할 인덱스 스키마 정의 (예: id, title, content, embedding)
(변경 없음) 이 부분은 클라우드 서비스를 그대로 활용하는 것이 훨씬 효율적입니다.
3. 데이터 준비 스크립트 구현 (로컬, 수동 실행)
3.1 run_analysis.py 스크립트 작성
(복귀) 이 스크립트는 내 컴퓨터에서 직접 python run_analysis.py로 실행합니다.
3.2 스크립트 세부 기능 구현
(1단계) 뉴스 수집: 네이버/구글 뉴스에서 원시 데이터를 가져옵니다.
(2단계) LLM 기반 키워드 추출: Azure OpenAI (GPT-4o) API를 호출하여 뉴스에서 키워드를 추출합니다.
(3단계) LLM 기반 카드뉴스 생성: 추출된 키워드를 Azure OpenAI (GPT-4o) API로 보내 분석 텍스트를 생성합니다.
(4단계) 텍스트 임베딩: 생성된 카드뉴스 텍스트를 Azure OpenAI (text-embedding-3-large) API를 통해 벡터로 변환합니다.
(5단계) Azure AI Search에 데이터 업로드: Azure AI Search SDK를 사용하여 준비된 텍스트와 벡터를 Azure의 인덱스에 업로드합니다.
4. API 서버 구현 (로컬 FastAPI 서버)
4.1 main.py FastAPI 애플리케이션 작성
(복귀) Uvicorn을 사용하여 uvicorn main:app --reload 명령으로 내 컴퓨터에서 서버를 실행합니다.
4.2 Azure AI Search 클라이언트 초기화
FastAPI 앱이 시작될 때 Azure AI Search 서비스에 연결하는 클라이언트 객체를 설정합니다.
4.3 분석 카드 조회 API 구현 (/cards)
Azure AI Search에 쿼리하여 저장된 카드뉴스 목록을 가져와 반환하는 GET 엔드포인트를 구현합니다.
4.4 RAG 챗봇 API 구현 (/chat)
(1단계) 질문 벡터화: 받은 질문을 Azure OpenAI API를 통해 벡터로 변환합니다.
(2단계) 유사 콘텐츠 검색: Azure AI Search 클라이언트를 통해 벡터 검색을 수행합니다.
(3단계) 최종 답변 생성: 검색된 내용을 컨텍스트로 Azure OpenAI API를 호출하여 답변을 생성하고 반환합니다.
5. 프론트엔드 연동 및 최종 테스트
5.1 로컬 API 서버 연동
(복귀) HTML/JavaScript 파일에서 http://127.0.0.1:8000 의 로컬 서버 엔드포인트를 호출하도록 설정합니다.
5.2 전체 흐름 테스트
(1단계) 데이터 준비: 터미널에서 python run_analysis.py를 실행하여 모든 데이터가 Azure AI Search에 저장되는 것을 확인합니다.
(2단계) 서버 실행: 다른 터미널에서 uvicorn main:app --reload를 실행합니다.
(3단계) 결과 확인: 웹 브라우저에서 index.html 파일을 열어 카드뉴스가 잘 표시되고 챗봇이 잘 작동하는지 확인합니다.