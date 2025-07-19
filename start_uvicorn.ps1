# Uvicorn으로 직접 서버 실행
Write-Host "Starting FastAPI server with uvicorn..." -ForegroundColor Green
Set-Location "c:\Users\NEW\Documents\GitHub\news_gpt_v2"

$uvicornPath = ".\venv\Scripts\uvicorn.exe"
if (Test-Path $uvicornPath) {
    Write-Host "Found uvicorn at: $uvicornPath" -ForegroundColor Yellow
    Write-Host "Starting server on http://localhost:8000" -ForegroundColor Cyan
    
    # uvicorn을 python 모듈로 실행
    & ".\venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000
} else {
    Write-Host "Uvicorn not found at: $uvicornPath" -ForegroundColor Red
    Write-Host "Please check the virtual environment" -ForegroundColor Red
}
Read-Host "Press Enter to exit"
