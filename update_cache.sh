#!/bin/bash
# Quick Start Script for Monthly Cache Update
# Gujarat Crop Price Forecasting System

echo "========================================"
echo "Gujarat Crop Price - Monthly Update"
echo "========================================"
echo

# Check if virtual environment exists
if [ ! -f ".venv/bin/activate" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please create it first: python -m venv .venv"
    echo "Then install dependencies: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

echo
echo "Checking API key..."
if [ -z "$DATA_GOV_API_KEY" ]; then
    echo
    echo "WARNING: DATA_GOV_API_KEY not set!"
    echo "Some data will be fetched from CSV fallback only."
    echo
    echo "To set API key:"
    echo "  export DATA_GOV_API_KEY=your_key_here"
    echo
    read -p "Continue anyway? (y/n): " continue
    if [ "$continue" != "y" ]; then
        exit 0
    fi
fi

echo
echo "========================================"
echo "Running Cache Update"
echo "========================================"
echo "This may take 20-40 minutes..."
echo

python update_monthly_cache.py

echo
echo "========================================"
echo "Update Complete!"
echo "========================================"
echo

echo "Checking cache status..."
python -c "import sys; sys.path.insert(0, 'src'); from src.monthly_cache import MonthlyDataCache; stats = MonthlyDataCache().get_cache_stats(); print(f'\nCache Statistics:\n  Last Updated: {stats[\"last_updated\"]}\n  Price Entries: {stats[\"total_price_entries\"]}\n  Rainfall Entries: {stats[\"total_rainfall_entries\"]}\n  NDVI Entries: {stats[\"total_ndvi_entries\"]}\n  Status: {\"✓ Current\" if stats[\"is_current\"] else \"⚠ Outdated\"}\n')"

echo
echo "Next steps:"
echo "  1. Test locally: python app.py"
echo "  2. Deploy to Hugging Face (see DEPLOYMENT_CHECKLIST.md)"
echo
