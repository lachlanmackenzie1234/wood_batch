@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo Wood Batch Windows Setup
echo ========================================
echo.

echo This setup checks for Git, Python, and VS Code.
echo It can install missing tools with winget if winget is available.
echo.

where winget >nul 2>nul
if errorlevel 1 (
    echo winget was not found.
    echo.
    echo Please install the following manually if missing:
    echo   Python: https://www.python.org/downloads/windows/
    echo   Git:    https://git-scm.com/download/win
    echo   VS Code: https://code.visualstudio.com/
    echo.
    echo After installing Python, make sure "Add python.exe to PATH" is enabled.
    echo.
    pause
    exit /b 1
)

echo Checking Git...
where git >nul 2>nul
if errorlevel 1 (
    echo Git was not found. Installing Git...
    winget install --id Git.Git -e --source winget
) else (
    echo Git found.
)

echo.
echo Checking Python...
where py >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Installing Python 3...
    winget install --id Python.Python.3 -e --source winget
    echo.
    echo IMPORTANT: after Python installs, close this window and run setup.bat again.
    echo This allows Windows PATH to refresh.
    echo.
    pause
    exit /b 0
) else (
    echo Python found.
)

echo.
echo Checking VS Code...
where code >nul 2>nul
if errorlevel 1 (
    echo VS Code was not found. Installing VS Code...
    winget install --id Microsoft.VisualStudioCode -e --source winget
) else (
    echo VS Code found.
)

echo.
echo Creating Python virtual environment if needed...
if not exist ".venv" (
    py -m venv .venv
    if errorlevel 1 (
        echo Failed to create the virtual environment.
        echo Please close this window, reopen it, and run setup.bat again.
        echo.
        pause
        exit /b 1
    )
) else (
    echo .venv already exists.
)

echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate the virtual environment.
    echo.
    pause
    exit /b 1
)

echo.
echo Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install Python dependencies.
    echo.
    pause
    exit /b 1
)

echo.
echo Checking Pillow...
python -c "from PIL import Image" >nul 2>nul
if errorlevel 1 (
    echo Pillow is not available. Installing Pillow directly...
    python -m pip install "Pillow>=10.4,<12"
)

echo.
echo Setup complete.
echo.
echo Next steps:
echo   1. Edit jobs.csv
echo   2. Edit config.csv if needed
echo   3. Double-click run.bat
echo.
echo To open the project in VS Code, run:
echo   code .
echo.
pause
