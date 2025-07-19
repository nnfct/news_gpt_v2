# 시스템 Python으로 직접 실행
Write-Host "Starting FastAPI server with system Python..." -ForegroundColor Green
Set-Location "c:\Users\NEW\Documents\GitHub\news_gpt_v2"

# 필요한 패키지 설치
Write-Host "Installing required packages..." -ForegroundColor Yellow
pip install fastapi uvicorn python-dotenv azure-search-documents openai requests

# 서버 실행
Write-Host "Starting server on http://localhost:8000" -ForegroundColor Cyan
python -m uvicorn main:app --host 0.0.0.0 --port 8000

Read-Host "Press Enter to exit"
