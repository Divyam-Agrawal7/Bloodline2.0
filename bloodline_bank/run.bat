@echo off
set PY=%~dp0..\bloodline2_project\.venv\Scripts\python.exe
start "Bloodline 2.0 detector" /D "%~dp0..\bloodline2_project" "%PY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
start "Bloodline Bank" /D "%~dp0" "%PY%" -m uvicorn app:app --host 127.0.0.1 --port 8001
timeout /t 6 >nul
start http://127.0.0.1:8001
