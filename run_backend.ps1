Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Zenith '26 College Fest Management System API   " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not detected. Creating one now..." -ForegroundColor Yellow
    python -m venv .venv
    & ".\.venv\Scripts\pip.exe" install -r requirements.txt
}

Write-Host "`nServer endpoints:" -ForegroundColor Green
Write-Host "  -> Student Portal:   http://127.0.0.1:8001/" -ForegroundColor White
Write-Host "  -> Admin Dashboard:  http://127.0.0.1:8001/admin.html" -ForegroundColor White
Write-Host "  -> Swagger API Docs: http://127.0.0.1:8001/docs" -ForegroundColor White

& ".\.venv\Scripts\uvicorn.exe" backend.main:app --host 127.0.0.1 --port 8001 --reload
