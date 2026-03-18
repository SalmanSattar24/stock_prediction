@echo off
REM Quick Setup Script for Stock Signal System (Windows)
REM This script helps you get up and running quickly on Windows

echo ======================================
echo Stock Signal System - Quick Setup
echo ======================================
echo.

REM Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python is not installed or not in PATH
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo [OK] Python %python_version% found
echo.

REM Step 1: Create virtual environment (optional but recommended)
if not exist "venv" (
    echo 1. Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
    echo     Activate with: venv\Scripts\activate
) else (
    echo [OK] Virtual environment already exists
)
echo.

REM Step 2: Install dependencies
echo 2. Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [X] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Step 3: Create .env file
echo 3. Setting up API keys...
if not exist ".env" (
    echo Creating .env file template...
    python config.py --setup
) else (
    echo [OK] .env file already exists
)
echo.

REM Step 4: Validate setup
echo 4. Validating configuration...
python config.py --validate
echo.

echo ======================================
echo Setup Complete!
echo ======================================
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Read SETUP_INSTRUCTIONS.md for Reddit setup
echo 3. Run: python test_system.py
echo 4. Check SYSTEM_GUIDE.md for usage examples
echo.
echo Need help?
echo + SETUP_INSTRUCTIONS.md - API key configuration
echo + SYSTEM_GUIDE.md - System overview and examples
echo + IMPLEMENTATION_SUMMARY.md - What was built
echo.
pause
