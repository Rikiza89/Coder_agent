@echo off
setlocal EnableDelayedExpansion

:: =============================================================================
:: run.bat — Agentic Coder ランチャー
:: このバッチファイルはagentic_coderフォルダと同じ階層に置くこと
:: 例: Desktop\run.bat と Desktop\agentic_coder\
:: =============================================================================

:: バッチファイル自身のディレクトリを作業ベースに設定する
:: これによりどこから実行しても正しいパスが解決される
cd /d "%~dp0"

echo.
echo  ==========================================
echo   Agentic Coder Launcher
echo  ==========================================
echo.

:: -----------------------------------------------------------------------------
:: Step 1: Pythonの存在確認
:: -----------------------------------------------------------------------------
echo [1/5] Checking Python installation...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Python not found in PATH.
    echo  Please install Python 3.10+ from https://python.org
    echo  and make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo  [OK] Found %PYTHON_VERSION%

:: -----------------------------------------------------------------------------
:: Step 2: agentic_coderパッケージの存在確認
:: -----------------------------------------------------------------------------
echo [2/5] Checking project structure...

if not exist "%~dp0agentic_coder\__init__.py" (
    echo.
    echo  [ERROR] agentic_coder package not found.
    echo  Expected structure:
    echo    %~dp0
    echo    └── agentic_coder\
    echo        └── __init__.py
    echo.
    echo  Make sure run.bat is in the PARENT folder of agentic_coder\
    echo.
    pause
    exit /b 1
)
echo  [OK] Project structure verified.

:: -----------------------------------------------------------------------------
:: Step 3: 仮想環境の作成（存在しない場合のみ）
:: 既存のvenvは再利用する — 毎回再作成しない
:: -----------------------------------------------------------------------------
echo [3/5] Setting up virtual environment...

if not exist "%~dp0.venv\Scripts\activate.bat" (
    echo  Creating new virtual environment...
    python -m venv "%~dp0.venv"
    if %errorlevel% neq 0 (
        echo.
        echo  [ERROR] Failed to create virtual environment.
        echo  Try running: python -m pip install virtualenv
        echo.
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created.
) else (
    echo  [OK] Existing virtual environment found, reusing.
)

:: -----------------------------------------------------------------------------
:: Step 4: 仮想環境を有効化してrequirementsをインストール
:: 依存パッケージが既にインストール済みの場合はスキップされる
:: -----------------------------------------------------------------------------
echo [4/5] Installing / verifying dependencies...

call "%~dp0.venv\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Failed to activate virtual environment.
    echo.
    pause
    exit /b 1
)

:: pip自体を最新化してから依存パッケージをインストール
python -m pip install --upgrade pip --quiet
python -m pip install requests psutil PySide6 pytest pytest-qt --quiet

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Failed to install dependencies.
    echo  Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)
echo  [OK] All dependencies satisfied.

:: -----------------------------------------------------------------------------
:: Step 5: アプリケーション起動
:: 仮想環境のPythonを明示的に使用する
:: -----------------------------------------------------------------------------
echo [5/5] Launching Agentic Coder...
echo.

"%~dp0.venv\Scripts\python.exe" -m agentic_coder

:: アプリが終了コード非ゼロで終了した場合にエラーを表示する
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Agentic Coder exited with error code %errorlevel%.
    echo  Check the log panel or console output above for details.
    echo.
    pause
)

endlocal