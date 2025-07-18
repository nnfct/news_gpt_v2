# PowerShell 스크립트로 FastAPI 서버 실행
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Set-Location "c:\Users\USER\Documents\GitHub\news_gpt_v2"
& "C:\Users\USER\Documents\GitHub\news_gpt_v2\.venv\Scripts\python.exe" main.py
Read-Host "Press Enter to exit"
