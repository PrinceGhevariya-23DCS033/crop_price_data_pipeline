#!/bin/bash
# Gujarat Crop Price Forecasting System - Startup Script
# Linux/Mac Bash Script

echo "================================================"
echo "Gujarat Crop Price Forecasting System"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run: python -m venv venv"
    echo "Then install dependencies: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "[1/3] Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "[WARNING] .env file not found!"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "Please edit .env and add your DATA_GOV_API_KEY"
    echo "Then run this script again."
    exit 1
fi

# Start API server
echo ""
echo "[2/3] Starting FastAPI server..."
echo "Server will be available at: http://localhost:8000"
echo "API docs will be at: http://localhost:8000/docs"
echo ""

cd src
python api.py &
API_PID=$!

# Wait for server to start
sleep 3

# Open browser (if available)
echo ""
echo "[3/3] Opening web interface..."

if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8000/docs
    xdg-open ../frontend/index.html
elif command -v open &> /dev/null; then
    open http://localhost:8000/docs
    open ../frontend/index.html
fi

echo ""
echo "================================================"
echo "Server is running!"
echo "================================================"
echo ""
echo "API Server: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: Open frontend/index.html in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Wait for user interrupt
wait $API_PID
