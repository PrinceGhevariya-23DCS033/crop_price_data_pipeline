@echo off
REM Gujarat Crop Price Forecasting System - Startup Script
REM Windows Batch Script

echo ================================================
echo Gujarat Crop Price Forecasting System
echo ================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then install dependencies: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo [WARNING] .env file not found!
    echo Creating from .env.example...
    copy .env.example .env
    echo.
    echo Please edit .env and add your DATA_GOV_API_KEY
    echo Then run this script again.
    pause
    exit /b 1
)

REM Start API server
echo.
echo [2/3] Starting FastAPI server...
echo Server will be available at: http://localhost:8000
echo API docs will be at: http://localhost:8000/docs
echo.

cd src
start "Crop Price API" python api.py

REM Wait a bit for server to start
timeout /t 3 /nobreak > nul

REM Open frontend
echo.
echo [3/3] Opening web interface...
cd ..\frontend

REM Try to open with default browser
start http://localhost:8000/docs
start index.html

echo.
echo ================================================
echo Server is running!
echo ================================================
echo.
echo API Server: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: Open frontend/index.html in your browser
echo.
echo Press Ctrl+C in the API window to stop the server
echo.
pause
