Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  NAVIAGENT - AUTOMATIZACION DOCUMENTAL MARITIMA" -ForegroundColor White
Write-Host "  Servidor Web Local en http://localhost:4000" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creando entorno virtual e instalando dependencias..." -ForegroundColor Yellow
    & "C:\Users\user\.local\bin\uv.exe" venv .venv
    & "C:\Users\user\.local\bin\uv.exe" pip install --python .venv\Scripts\python.exe -r requirements.txt
}

Write-Host "Lanzando servidor Uvicorn en http://localhost:4000..." -ForegroundColor Cyan
Start-Process "http://localhost:4000"
& ".venv\Scripts\python.exe" -m uvicorn src.main:app --host 0.0.0.0 --port 4000 --reload
