@echo off
echo ================================================
echo    News GPT v2 - 환경 설정 스크립트
echo ================================================
echo.

REM Python 버전 확인
echo [1/6] Python 버전 확인 중...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python이 설치되지 않았거나 PATH에 없습니다.
    echo Python 3.10 이상을 설치해주세요: https://python.org
    pause
    exit /b 1
)
echo.

REM 가상환경 생성
echo [2/6] 가상환경 생성 중...
if not exist .venv (
    python -m venv .venv
    echo ✅ 가상환경이 생성되었습니다.
) else (
    echo ✅ 가상환경이 이미 존재합니다.
)
echo.

REM 가상환경 활성화
echo [3/6] 가상환경 활성화 중...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: 가상환경 활성화에 실패했습니다.
    pause
    exit /b 1
)
echo ✅ 가상환경이 활성화되었습니다.
echo.

REM pip 업그레이드
echo [4/6] pip 업그레이드 중...
python -m pip install --upgrade pip
echo.

REM 의존성 설치
echo [5/6] 패키지 설치 중...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: 패키지 설치에 실패했습니다.
    pause
    exit /b 1
)
echo ✅ 모든 패키지가 설치되었습니다.
echo.

REM .env 파일 확인
echo [6/6] 환경 설정 파일 확인 중...
if not exist .env (
    echo WARNING: .env 파일이 없습니다.
    echo 프로젝트 실행을 위해 .env 파일을 생성하고 API 키를 설정해주세요.
    echo.
    echo 예시:
    echo OPENAI_API_KEY=your_openai_key_here
    echo AZURE_SEARCH_ENDPOINT=your_azure_endpoint
    echo AZURE_SEARCH_KEY=your_azure_key
    echo DEEPSEARCH_API_KEY=your_deepsearch_key
) else (
    echo ✅ .env 파일이 존재합니다.
)
echo.

echo ================================================
echo    🎉 환경 설정이 완료되었습니다!
echo ================================================
echo.
echo 서버 실행 방법:
echo   1. .venv\Scripts\activate.bat
echo   2. python main.py
echo.
echo 또는 start_server.bat 파일을 실행하세요.
echo.
pause
