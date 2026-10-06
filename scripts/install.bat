@echo off
setlocal
set "VENV=.venv"
if "%1"=="--venv" set "VENV=%2"
py -m venv "%VENV%"
"%VENV%\Scripts\python.exe" -m pip install -e .
if "%1"=="--no-key-wizard" goto done
"%VENV%\Scripts\lwa-router.exe" init
:done
echo Lwa MCP installed. Use %VENV%\Scripts\lwa-web.exe to start the web surface.
