@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: Force working directory to this file's location
cd /d "%~dp0"

echo.
echo ==========================================
echo   Agentic Coder Launcher
echo ==========================================
echo.

:: -----------------------------------------------------------------------------
:: Step 1 - Check Python
:: -----------------------------------------------------------------------------
echo [1/5] Checking Python installation...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python not found in PATH.
    echo Install Python 3.10+ and check "Add Python to PATH".
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Found !PYVER!

:: -----------------------------------------------------------------------------
:: Step 2 - Check project structure
:: -----------------------------------------------------------------------------
echo [2/5] Checking project structure...

if not exist "agentic_coder\__init__.py" (
    echo.
    echo [ERROR] agentic_coder package not found.
    echo Make sure this file is in the parent folder of agentic_coder\
    echo.
    pause
    exit /b 1
)

echo [OK] Project structure verified.

:: -----------------------------------------------------------------------------
:: Step 3 - Create virtual environment if missing
:: -----------------------------------------------------------------------------
echo [3/5] Setting up virtual environment...

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...

    python -m venv venv 2>nul

    if %errorlevel% neq 0 (
        echo Attempting ensurepip repair...
        python -m ensurepip --upgrade
        python -m venv venv
    )

    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to create virtual environment.
        echo Your Python installation may be corrupted.
        echo Reinstall from python.org if necessary.
        echo.
        pause
        exit /b 1
    )

    echo [OK] Virtual environment created.
) else (
    echo [OK] Existing virtual environment found.
)

:: -----------------------------------------------------------------------------
:: Step 4 - Install dependencies
:: -----------------------------------------------------------------------------
echo [4/5] Installing / verifying dependencies...

set VENV_PY=venv\Scripts\python.exe

"%VENV_PY%" -m pip install --upgrade pip --quiet
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] pip upgrade failed.
    pause
    exit /b 1
)

"%VENV_PY%" -m pip install requests psutil PySide6 pytest pytest-qt --quiet
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Dependency installation failed.
    echo Check internet connection.
    echo.
    pause
    exit /b 1
)

echo [OK] Dependencies ready.

:: -----------------------------------------------------------------------------
:: Step 5 - Launch application
:: -----------------------------------------------------------------------------
echo [5/5] Launching Agentic Coder...
echo.

"%VENV_PY%" -m agentic_coder
set EXITCODE=%errorlevel%

if %EXITCODE% neq 0 (
    echo.
    echo [ERROR] Application exited with code %EXITCODE%.
    echo.
    pause
)

endlocal
exit /b %EXITCODE%