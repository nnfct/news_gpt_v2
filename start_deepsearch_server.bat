@echo off
REM DeepSearch API 서버 시작 스크립트
cd /d "%~dp0"
echo 🚀 DeepSearch API 서버 시작 중...
echo.

echo 📋 가상환경 활성화...
call .\venv_new\Scripts\activate.bat

echo 📋 환경 변수 확인...
if not exist .env (
    echo ❌ .env 파일이 없습니다!
    pause
    exit /b 1
)

echo 📋 필요한 패키지 확인...
python -c "import fastapi, uvicorn, azure.search.documents, openai" 2>nul
if %errorlevel% neq 0 (
    echo ❌ 필요한 패키지가 설치되지 않았습니다!
    echo 패키지 설치 중...
    pip install -r requirements.txt
)

echo 📋 서버 시작...
echo 🌐 서버 주소: http://localhost:8003
echo 🔧 관리자 모드: Ctrl+C로 종료
echo.

python main.py

pause
