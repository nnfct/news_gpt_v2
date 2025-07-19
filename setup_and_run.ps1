# 가상환경 재생성 및 서버 실행
Write-Host "Creating new virtual environment..." -ForegroundColor Green
Set-Location "c:\Users\NEW\Documents\GitHub\news_gpt_v2"

# 기존 가상환경 백업
if (Test-Path "venv_new") {
    Write-Host "Backing up old virtual environment..." -ForegroundColor Yellow
    if (Test-Path "venv_old") {
        Remove-Item "venv_old" -Recurse -Force
    }
    Rename-Item "venv_new" "venv_old"
}

# 새 가상환경 생성
Write-Host "Creating new virtual environment..." -ForegroundColor Cyan
python -m venv venv_new

# 가상환경 활성화 및 패키지 설치
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".\venv_new\Scripts\Activate.ps1"

Write-Host "Installing required packages..." -ForegroundColor Cyan
& ".\venv_new\Scripts\pip.exe" install -r requirements.txt

# 서버 실행
Write-Host "Starting FastAPI server..." -ForegroundColor Green
& ".\venv_new\Scripts\uvicorn.exe" main:app --host 0.0.0.0 --port 8000

Read-Host "Press Enter to exit"
