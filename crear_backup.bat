@echo off
chcp 65001 > nul
title NaviAgent - Generador de Copia de Seguridad
echo =========================================================
echo   NAVIAGENT - CREANDO COPIA DE SEGURIDAD DEL PROYECTO
echo =========================================================
echo.

cd /d "%~dp0"

IF EXIST ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe backup.py
) ELSE (
    python backup.py
)

echo.
pause
