@echo off
echo ================================================
echo    News GPT v2 - 서버 시작
echo ================================================
echo.

REM 가상환경 확인 및 활성화
if not exist venv (
    echo ERROR: 가상환경이 없습니다. setup.bat을 먼저 실행해주세요.
    pause
    exit /b 1
)

echo [1/3] 가상환경 활성화 중...
call venv\Scripts\activate.bat
echo ✅ 가상환경 활성화 완료
echo.

REM 필요한 패키지 확인
echo [2/3] 의존성 확인 중...
python -c "import fastapi, uvicorn, openai, pandas" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: 일부 패키지가 누락되었습니다. 설치 중...
    pip install -r requirements.txt
)
echo ✅ 의존성 확인 완료
echo.

REM .env 파일 확인
if not exist .env (
    echo WARNING: .env 파일이 없습니다. API 키 설정이 필요할 수 있습니다.
    echo.
)

REM 서버 시작
echo [3/3] 서버 시작 중...
echo 서버 주소: http://localhost:8000
echo 종료하려면 Ctrl+C를 누르세요.
echo.
python main.py

pause
