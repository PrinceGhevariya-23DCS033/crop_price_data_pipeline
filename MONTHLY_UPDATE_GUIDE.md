# Monthly Cache Update - Quick Reference
# Gujarat Crop Price Forecasting System

## 📅 Schedule: Run between 20-25th of each month

### Why This Schedule?
- **NDVI data** becomes available 16-20 days after month end
- **Mandi prices** need time to reflect monthly patterns  
- **Rainfall data** for previous month is complete by 20th

---

## 🚀 Quick Update Steps

### 1. Activate Environment
```bash
cd D:\SEM_six_SGP\Crop_Price_V2

# Activate virtual environment
.venv\Scripts\activate  # Windows
# OR
source .venv/bin/activate  # Linux/Mac
```

### 2. Run Update Script
```bash
# Update all data (recommended)
python update_monthly_cache.py

# OR update specific components:
python update_monthly_cache.py --prices-only
python update_monthly_cache.py --rainfall-only
python update_monthly_cache.py --ndvi-only
```

### 3. Verify Update
```bash
python -c "import sys; sys.path.insert(0, 'src'); from src.monthly_cache import MonthlyDataCache; stats = MonthlyDataCache().get_cache_stats(); print(f'Updated: {stats[\"last_updated\"]}\nPrices: {stats[\"total_price_entries\"]}\nRainfall: {stats[\"total_rainfall_entries\"]}\nNDVI: {stats[\"total_ndvi_entries\"]}\nStatus: {\"✓ Current\" if stats[\"is_current\"] else \"⚠ Outdated\"}')"
```

### 4. Test Locally (Optional)
```bash
# Start Gradio app
python app.py

# Open http://localhost:7860
# Test a few predictions
```

### 5. Deploy to Hugging Face
```bash
# Navigate to HF repo
cd ../crop-price-forecast  # Or your HF repo location

# Copy updated cache
cp -r ../Crop_Price_V2/monthly_cache .

# Commit and push
git add monthly_cache/cache_metadata.json
git add monthly_cache/prices/
git add monthly_cache/rainfall/
git add monthly_cache/ndvi/
git commit -m "Cache update: $(date +'%B %Y')"
git push

# HF will auto-deploy in 2-3 minutes
```

---

## 📊 What Gets Updated?

### Price Cache (45 crops × 33 districts = 1,485 entries)
- 30-day average mandi prices
- Number of trading days
- Data source (API/CSV)

### Rainfall Cache (33 districts)
- Monthly rainfall sum (mm)
- Mean daily rainfall (mm/day)
- Number of rainy days

### NDVI Cache (33 districts)
- Mean NDVI value (0-1)
- Vegetation health indicator
- Previous month's satellite data

---

## ⚠️ Common Issues & Fixes

### "DATA_GOV_API_KEY not found"
```bash
# Set API key in environment
export DATA_GOV_API_KEY="your_key_here"  # Linux/Mac
# OR
set DATA_GOV_API_KEY=your_key_here  # Windows CMD
# OR
$env:DATA_GOV_API_KEY="your_key_here"  # Windows PowerShell
```

### "No API data available, using CSV fallback"
✓ This is normal! CSV fallback ensures complete coverage.

### "Warning: NDVI data not current"
- Run update after 20th of the month
- NDVI data lags by 16-20 days

### Update takes too long
```bash
# Update components separately
python update_monthly_cache.py --prices-only  # ~15-30 min
python update_monthly_cache.py --rainfall-only  # ~5 min
python update_monthly_cache.py --ndvi-only  # ~3 min
```

---

## 📝 Monthly Checklist

```
[ ] Run update script between 20-25th
[ ] Verify all components updated successfully
[ ] Check cache statistics
[ ] Test 2-3 predictions locally
[ ] Commit cache to git
[ ] Push to Hugging Face
[ ] Verify HF Space rebuilt
[ ] Test predictions on HF Space
[ ] Document month in log (see below)
```

---

## 📋 Update Log Template

Keep a simple log in `cache_update_log.txt`:

```
2024-02 | 2024-02-20 | ✓ All | 1485 prices, 33 rainfall, 33 NDVI | Deployed
2024-03 | 2024-03-22 | ✓ All | 1485 prices, 33 rainfall, 33 NDVI | Deployed
2024-04 | 2024-04-20 | ⚠ Partial | 1420 prices (65 failed), 33 rainfall, 33 NDVI | API timeout for some crops
```

Format: `Year-Month | Update Date | Status | Stats | Notes`

---

## 🔄 Automation (Advanced)

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Monthly → 20th at 2:00 AM
4. Action: Start a program
   - Program: `D:\SEM_six_SGP\Crop_Price_V2\.venv\Scripts\python.exe`
   - Arguments: `update_monthly_cache.py`
   - Start in: `D:\SEM_six_SGP\Crop_Price_V2`

### Linux Cron

```bash
# Edit crontab
crontab -e

# Add this line (runs at 2 AM on 20th of each month)
0 2 20 * * cd /path/to/Crop_Price_V2 && .venv/bin/python update_monthly_cache.py >> cache_update.log 2>&1
```

---

## 💡 Pro Tips

1. **Set a calendar reminder** for 20th of each month
2. **Run before 25th** to ensure data is current
3. **Keep update logs** for troubleshooting
4. **Test locally first** before deploying to HF
5. **Monitor HF Space logs** after deployment
6. **Backup cache folder** before major updates

---

## 📞 Emergency Contact

If update fails or HF deployment breaks:

1. Check update script logs
2. Verify API keys are set
3. Test cache manually:
   ```python
   from src.monthly_cache import MonthlyDataCache
   cache = MonthlyDataCache()
   print(cache.get_cache_stats())
   ```
4. Restore from backup if needed
5. Contact maintainer: [your-email@example.com]

---

## ✅ Expected Output

```
======================================================================
 GUJARAT CROP PRICE FORECASTING - MONTHLY CACHE UPDATE
======================================================================
Update Date: 2024-02-20 10:30:00
Target Period: 2024-02

======================================================================
INITIALIZING
======================================================================
✓ Price fetcher initialized
✓ Weather fetcher initialized
✓ NDVI fetcher initialized

Found 45 commodities
Found 33 districts

======================================================================
📊 UPDATING PRICE CACHE
======================================================================

[1/1485] Wheat - Ahmedabad
  ✓ Price: ₹2850.50 (API: Average of last 28 days)
[2/1485] Wheat - Amreli
  ✓ Price: ₹2820.00 (CSV: Average of last 30 days)
...

======================================================================
Price Cache Update: 1420 success, 65 failed
======================================================================

======================================================================
🌧️  UPDATING RAINFALL CACHE
======================================================================
Fetching data for: 2024-01

[1/33] Ahmedabad
  ✓ Rainfall: 12.5mm (avg: 0.4mm/day)
...

======================================================================
Rainfall Cache Update: 33 success, 0 failed
======================================================================

======================================================================
🛰️  UPDATING NDVI CACHE
======================================================================
Fetching data for: 2024-01

[1/33] Ahmedabad
  ✓ NDVI: 0.6523 (source: CSV)
...

======================================================================
NDVI Cache Update: 33 success, 0 failed
======================================================================

======================================================================
✅ CACHE UPDATE COMPLETE
======================================================================

Cache Statistics:
  Last Updated: 2024-02-20T10:45:23.123456
  Period: 2024-02
  Price Entries: 1485
  Rainfall Entries: 33
  NDVI Entries: 33
  Commodities: 45
  Districts: 33
  Status: ✓ Current

======================================================================
Next update recommended: 20-25th of next month
======================================================================
```

---

**Remember:** Consistency is key! Set a monthly reminder and stick to the 20-25th schedule.
