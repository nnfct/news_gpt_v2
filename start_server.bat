@echo off
cd /d "c:\Users\NEW\Documents\GitHub\news_gpt_v2"
echo Starting FastAPI server...
echo Checking Python path...
if exist "venv\Scripts\python.exe" (
    echo Found Python at: venv\Scripts\python.exe
    "venv\Scripts\python.exe" main.py
) else (
    echo Python not found in venv\Scripts\
    echo Please check the virtual environment
)
pause
