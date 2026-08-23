@echo off
setlocal
set "ROOT=%~dp0.."
if defined LWA_PYTHON (
  "%LWA_PYTHON%" -m lwa_mcp.launch %*
) else (
  "%ROOT%\.venv\Scripts\python.exe" -m lwa_mcp.launch %*
)
exit /b %ERRORLEVEL%
