@echo off
echo Starting Zenith '26 College Fest Management System API...
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Server running at http://127.0.0.1:8001
echo Student Portal: http://127.0.0.1:8001/
echo Admin Dashboard: http://127.0.0.1:8001/admin.html
echo API Docs: http://127.0.0.1:8001/docs
uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
pause
