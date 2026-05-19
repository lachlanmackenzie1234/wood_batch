@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo Wood Batch Template Generator
echo ========================================
echo.

where py >nul 2>nul
if errorlevel 1 (
    echo Python was not found.
    echo.
    echo Please install Python first:
    echo   1. Go to https://www.python.org/downloads/windows/
    echo   2. Download the latest Python 3 installer
    echo   3. Run the installer
    echo   4. IMPORTANT: tick "Add python.exe to PATH"
    echo   5. Re-open this folder and run run.bat again
    echo.
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo requirements.txt was not found in this folder.
    echo Expected file: %cd%\requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist "template.py" (
    echo template.py was not found in this folder.
    echo Expected file: %cd%\template.py
    echo.
    pause
    exit /b 1
)

if not exist "output" mkdir "output"

if not exist ".venv" (
    echo Creating Python virtual environment...
    py -m venv .venv
    if errorlevel 1 (
        echo Failed to create the virtual environment.
        echo Please check that Python 3 is installed correctly.
        echo.
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate the virtual environment.
    echo.
    pause
    exit /b 1
)

echo Installing/updating Python dependencies...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip.
    echo.
    pause
    exit /b 1
)

for %%A in (requirements.txt) do set REQUIREMENTS_SIZE=%%~zA
if "%REQUIREMENTS_SIZE%"=="0" (
    echo requirements.txt is empty. Installing Pillow directly...
    python -m pip install "Pillow>=10.4,<12"
) else (
    python -m pip install -r requirements.txt
)
if errorlevel 1 (
    echo Failed to install Python dependencies.
    echo.
    pause
    exit /b 1
)

echo Checking Pillow installation...
python -c "from PIL import Image" >nul 2>nul
if errorlevel 1 (
    echo Pillow is not available after installing requirements. Installing Pillow directly...
    python -m pip install "Pillow>=10.4,<12"
    if errorlevel 1 (
        echo Failed to install Pillow.
        echo.
        pause
        exit /b 1
    )
)

echo.
echo Running template generator...
python template.py
if errorlevel 1 (
    echo.
    echo Template generation failed.
    echo Check jobs.csv, template.py, and the images folder.
    echo.
    pause
    exit /b 1
)

echo.
echo Done. Check the output folder.
echo.
pause
