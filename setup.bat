@echo off
REM YouTube to Article Converter - Setup Script (Windows)
REM This script helps you get started with the YouTube to Article Converter

echo ==========================================
echo YouTube to Article Converter - Setup
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3 is not installed.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Found Python:
python --version
echo.

REM Navigate to project directory
cd /d "%~dp0\youtube_to_article"

REM Check if .env exists
if exist .env (
    echo.
    echo .env file already exists!
    set /p OVERWRITE="Do you want to overwrite it? (y/N): "
    if /i not "%OVERWRITE%"=="y" (
        echo Keeping existing .env file...
    ) else (
        echo Creating new .env from template...
        copy /Y .env.example .env >nul
        echo Created .env file
    )
) else (
    echo Creating .env from template...
    if not exist .env.example (
        echo Error: .env.example not found!
        pause
        exit /b 1
    )
    copy .env.example .env >nul
    echo Created .env file
)

echo.
echo ==========================================
echo HuggingFace API Token Setup
echo ==========================================
echo.
echo You need a HuggingFace API token to use this tool.
echo Get your token at: https://huggingface.co/settings/tokens
echo.
set /p HF_TOKEN="Enter your HuggingFace API token (or press Enter to skip): "

if not "%HF_TOKEN%"=="" (
    REM Update the .env file with the token using PowerShell
    powershell -Command "(Get-Content .env) -replace 'HF_TOKEN=.*', 'HF_TOKEN=%HF_TOKEN%' | Set-Content .env"
    echo HuggingFace token configured
) else (
    echo Skipped token configuration. You'll need to edit .env manually.
)

echo.
echo ==========================================
echo Installing Python Dependencies
echo ==========================================
echo.

REM Check if virtual environment should be created
if not exist venv (
    set /p CREATE_VENV="Create a virtual environment? (recommended) (Y/n): "
    if /i not "%CREATE_VENV%"=="n" (
        echo Creating virtual environment...
        python -m venv venv
        echo Virtual environment created

        REM Activate virtual environment
        call venv\Scripts\activate.bat
        echo Virtual environment activated
    )
)

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt
echo Dependencies installed

echo.
echo ==========================================
echo Checking FFmpeg Installation
echo ==========================================
echo.

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo FFmpeg not found in PATH
    echo The tool will attempt to auto-detect FFmpeg, but you may need to:
    echo   1. Install FFmpeg: https://ffmpeg.org/download.html
    echo   2. Add it to your PATH, or
    echo   3. Set FFMPEG_PATH in your .env file
) else (
    echo FFmpeg is installed:
    ffmpeg -version | findstr "ffmpeg version"
)

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo   1. If you haven't already, add your HuggingFace token to .env
echo   2. Launch the app:
echo.
if exist venv (
    echo      venv\Scripts\activate     # Activate virtual environment
)
echo      streamlit run app.py
echo.
echo   3. Open your browser at http://localhost:8501
echo.
echo Happy converting! 🎥 -^> 📝
echo.
pause
