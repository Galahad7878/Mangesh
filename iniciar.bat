@echo off
chcp 65001 > nul
title NaviAgent - Servidor Web LAN (Unidad F:\)
echo =================================================================
echo   NAVIAGENT - SERVIDOR WEB LOCAL Y RED DE AREA LOCAL (LAN)
echo   Generacion de Cartas de Invitacion (LOI) y Anexo IX
echo =================================================================
echo.
echo [*] Directorio de Plantillas: F:\Letters of Invitation LOIs\
echo [*] Directorio de Salida:     F:\Letters of Invitation LOIs\Documentos_Generados\
echo.

cd /d "%~dp0"
set "PYTHONPATH=."

REM Detectar IP local LAN de forma segura sin romper bloques cmd
set "LOCAL_IP="
for /f "tokens=4" %%a in ('route print 0.0.0.0 2^>nul ^| findstr /c:" 0.0.0.0"') do set "LOCAL_IP=%%a"

echo [*] Acceso local - este equipo:          http://localhost:4000
if defined LOCAL_IP echo [*] Acceso red local - otros equipos:    http://%LOCAL_IP%:4000
echo.
echo =================================================================
echo   Iniciando servidor en 0.0.0.0:4000 ...
echo   (No cierres esta ventana mientras uses la aplicacion)
echo =================================================================
echo.

start http://localhost:4000

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m uvicorn src.main:app --host 0.0.0.0 --port 4000
) else (
    python -m uvicorn src.main:app --host 0.0.0.0 --port 4000
)

echo.
echo El servidor se ha detenido.
pause
