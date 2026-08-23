@echo off
setlocal EnableExtensions

set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "PYTHON_BIN=%PYTHON_BIN%"
if not defined PYTHON_BIN set "PYTHON_BIN=py -3.11"
set "VENV_DIR=%LWA_VENV_DIR%"
if not defined VENV_DIR set "VENV_DIR=%ROOT%\.venv"
set "RUN_WIZARD=1"
set "WITH_DEV=0"
set "UPGRADE_PIP=0"

:args
if "%~1"=="" goto install
if /I "%~1"=="--no-key-wizard" set "RUN_WIZARD=0" & shift & goto args
if /I "%~1"=="--with-dev" set "WITH_DEV=1" & shift & goto args
if /I "%~1"=="--upgrade-pip" set "UPGRADE_PIP=1" & shift & goto args
if /I "%~1"=="--help" goto help
if /I "%~1"=="-h" goto help
echo Unknown option: %~1
goto fail

:install
if not exist "%ROOT%\pyproject.toml" (
  echo pyproject.toml not found under %ROOT%
  goto fail
)
if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo Creating virtual environment: %VENV_DIR%
  %PYTHON_BIN% -m venv "%VENV_DIR%"
  if errorlevel 1 goto fail
)
if "%UPGRADE_PIP%"=="1" "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
if "%WITH_DEV%"=="1" (
  "%VENV_DIR%\Scripts\python.exe" -m pip install -e "%ROOT%[dev]"
) else (
  "%VENV_DIR%\Scripts\python.exe" -m pip install -e "%ROOT%"
)
if errorlevel 1 goto fail
if "%RUN_WIZARD%"=="1" (
  "%VENV_DIR%\Scripts\lwa-router.exe" init
) else (
  "%VENV_DIR%\Scripts\lwa-router.exe" init --no-key-wizard
)
if errorlevel 1 goto fail

echo.
echo Installed Lwa MCP successfully.
echo.
echo Launch from this environment:
echo   "%VENV_DIR%\Scripts\lwa.exe"
echo   "%VENV_DIR%\Scripts\lwa-web.exe"
echo.
echo Or activate the environment first:
echo   "%VENV_DIR%\Scripts\activate.bat"
goto done

:help
echo Usage: scripts\install.bat [--no-key-wizard] [--with-dev] [--upgrade-pip]
goto done

:fail
exit /b 1

:done
exit /b 0
