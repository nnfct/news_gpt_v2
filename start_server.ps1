# PowerShell 스크립트로 FastAPI 서버 실행
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Set-Location "c:\Users\NEW\Documents\GitHub\news_gpt_v2"

$pythonPath = ".\venv\Scripts\python.exe"
if (Test-Path $pythonPath) {
    Write-Host "Found Python at: $pythonPath" -ForegroundColor Yellow
    Write-Host "Starting server on http://localhost:8000" -ForegroundColor Cyan
    
    # 환경 변수 정리
    $env:PYTHONPATH = ""
    
    # 직접 실행
    & $pythonPath main.py
} else {
    Write-Host "Python not found at: $pythonPath" -ForegroundColor Red
    Write-Host "Please check the virtual environment" -ForegroundColor Red
}
Read-Host "Press Enter to exit"
