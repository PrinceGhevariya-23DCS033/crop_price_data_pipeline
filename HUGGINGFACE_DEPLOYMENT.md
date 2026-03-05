# Hugging Face Deployment Guide
## Gujarat Crop Price Forecasting System

This guide explains how to deploy the crop price forecasting system to Hugging Face Spaces using monthly cached data for fast predictions.

---

## 🎯 Overview

The system uses **monthly cached data** instead of real-time API calls, which:
- ✅ Makes predictions **10-100x faster** (sub-second response)
- ✅ Avoids API rate limits and authentication issues
- ✅ Works reliably on Hugging Face Spaces
- ✅ Reduces infrastructure costs
- ✅ More predictable behavior

### Monthly Update Schedule

Data is cached monthly after **16-20th** when NDVI satellite data becomes available:

```
Month 1 (20-25th) → Fetch & cache data → Deploy to HF
Month 2 (1-19th)  → Users get predictions from cache (fast!)
Month 2 (20-25th) → Update cache → Redeploy to HF
...and so on
```

---

## 📋 Prerequisites

### 1. **Prepare Monthly Cache**

Before deploying, run the monthly update script to populate the cache:

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate  # Windows

# Run cache update (run between 20-25th of each month)
python update_monthly_cache.py

# This will fetch:
# - Latest mandi prices (30-day average)
# - Rainfall data (previous month)
# - NDVI data (previous month)
```

This creates a `monthly_cache/` directory with:
```
monthly_cache/
├── cache_metadata.json
├── prices/
│   ├── wheat_ahmedabad.json
│   ├── cotton_rajkot.json
│   └── ...
├── rainfall/
│   ├── ahmedabad.json
│   ├── rajkot.json
│   └── ...
└── ndvi/
    ├── ahmedabad.json
    ├── rajkot.json
    └── ...
```

### 2. **Verify Cache**

Check cache status:

```bash
python -c "
import sys; sys.path.insert(0, 'src')
from src.monthly_cache import MonthlyDataCache
cache = MonthlyDataCache()
stats = cache.get_cache_stats()
print(f'Price entries: {stats[\"total_price_entries\"]}')
print(f'Last updated: {stats[\"last_updated\"]}')
print(f'Is current: {stats[\"is_current\"]}')
"
```

Expected output:
```
Price entries: 1485  # (45 crops × 33 districts)
Last updated: 2024-02-20T15:30:00
Is current: True
```

---

## 🚀 Deployment Steps

### Option 1: Deploy via Hugging Face Web Interface

1. **Create a New Space:**
   - Go to https://huggingface.co/new-space
   - Choose **Gradio** as the SDK
   - Select **CPU Basic** (free tier works fine)
   - Make it **Public** or **Private**

2. **Upload Files:**
   
   Upload these files/directories to your Space:

   ```
   Required Files:
   ✅ app.py                        # Main Gradio app
   ✅ requirements_hf.txt           # Rename to requirements.txt
   ✅ src/                          # All Python modules
   ✅ production_model/             # Trained models
   ✅ processed/                    # Historical data CSVs
   ✅ monthly_cache/                # **IMPORTANT: Pre-generated cache**
   ✅ district_latlon.csv           # District coordinates
   ✅ README.md                     # Documentation
   ```

   **IMPORTANT:** The `monthly_cache/` directory MUST be included with pre-populated data!

3. **Configure Space:**
   
   In your Space settings:
   - **SDK:** Gradio
   - **Python version:** 3.10
   - **Hardware:** CPU Basic (free)
   - **Persistent storage:** Not required (cache in repo)

4. **Space will automatically build and deploy!**

### Option 2: Deploy via Git (Recommended for Updates)

```bash
# Clone your HF Space repository
git clone https://huggingface.co/spaces/YOUR_USERNAME/crop-price-forecast
cd crop-price-forecast

# Copy files
cp ../Crop_Price_V2/app.py .
cp ../Crop_Price_V2/requirements_hf.txt requirements.txt
cp -r ../Crop_Price_V2/src .
cp -r ../Crop_Price_V2/production_model .
cp -r ../Crop_Price_V2/processed .
cp -r ../Crop_Price_V2/monthly_cache .  # **Critical!**
cp ../Crop_Price_V2/district_latlon.csv .

# Commit and push
git add .
git commit -m "Initial deployment with cached data"
git push

# HF will automatically rebuild
```

---

## 🔄 Monthly Update Workflow

To keep predictions current, update cache monthly:

### Step 1: Generate Fresh Cache (Local)

Run between **20-25th** of each month:

```bash
# On your local machine
cd Crop_Price_V2
source .venv/bin/activate

# Update cache with latest data
python update_monthly_cache.py

# Verify update
python -c "
import sys; sys.path.insert(0, 'src')
from src.monthly_cache import MonthlyDataCache
print(MonthlyDataCache().get_cache_stats())
"
```

### Step 2: Deploy to Hugging Face

```bash
# Copy updated cache to HF repo
cd ../crop-price-forecast
cp -r ../Crop_Price_V2/monthly_cache .

# Commit and push
git add monthly_cache/
git commit -m "Update cache for $(date +'%Y-%m')"
git push

# HF will auto-deploy in ~2-3 minutes
```

### Automation (Optional)

Set up a monthly cron job or GitHub Action:

```yaml
# .github/workflows/update-cache.yml
name: Monthly Cache Update

on:
  schedule:
    - cron: '0 2 20 * *'  # 2 AM on 20th of each month
  workflow_dispatch:  # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Update cache
        env:
          DATA_GOV_API_KEY: ${{ secrets.DATA_GOV_API_KEY }}
        run: python update_monthly_cache.py
      
      - name: Commit and push
        run: |
          git config user.name "Cache Bot"
          git config user.email "bot@example.com"
          git add monthly_cache/
          git commit -m "Auto-update cache $(date +'%Y-%m-%d')"
          git push
```

---

## 📊 Cache Structure Explained

### Price Cache
```json
// monthly_cache/prices/wheat_ahmedabad.json
{
  "commodity": "Wheat",
  "district": "Ahmedabad",
  "year": 2024,
  "month": 2,
  "cached_at": "2024-02-20T10:30:00",
  "monthly_mean_price": 2850.50,
  "days_traded": 28,
  "price_source": "API: Average of last 28 days",
  "data_source": "API"
}
```

### Rainfall Cache
```json
// monthly_cache/rainfall/ahmedabad.json
{
  "district": "Ahmedabad",
  "year": 2024,
  "month": 1,
  "cached_at": "2024-02-20T10:35:00",
  "monthly_rain_sum": 12.5,
  "monthly_rain_mean": 0.4,
  "rain_days": 3
}
```

### NDVI Cache
```json
// monthly_cache/ndvi/ahmedabad.json
{
  "district": "Ahmedabad",
  "year": 2024,
  "month": 1,
  "cached_at": "2024-02-20T10:40:00",
  "monthly_ndvi_mean": 0.6523,
  "source": "CSV"
}
```

---

## 🧪 Testing Before Deployment

### Local Testing

```bash
# Test the Gradio app locally
python app.py

# App will be available at http://localhost:7860
```

### Test Cache Integration

```python
# test_cache_integration.py
import sys
sys.path.insert(0, 'src')

from src.cached_fetcher import CachedDataFetcher

# Test fetcher
fetcher = CachedDataFetcher(use_api_fallback=False)

# Get cache status
status = fetcher.get_cache_status()
print("Cache Status:", status)

# Test data retrieval
data = fetcher.get_all_data("Wheat", "Ahmedabad", 2024, 2)
print("\nSample Data:", data)

# Verify we have price
assert data['current_price'] is not None, "Price data missing!"
print("\n✅ Cache integration working!")
```

---

## 🔍 Troubleshooting

### Issue: "No Price Data Available"

**Cause:** Cache not populated or commodity-district combination missing

**Solution:**
```bash
# Run update script with verbose output
python update_monthly_cache.py --prices-only

# Check specific commodity
python -c "
import sys, os; sys.path.insert(0, 'src')
from src.monthly_cache import MonthlyDataCache
cache = MonthlyDataCache()
data = cache.get_price('Wheat', 'Ahmedabad')
print(data)
"
```

### Issue: "Cache is Outdated"

**Cause:** Cache metadata shows old update date

**Solution:**
```bash
# Force cache refresh
python update_monthly_cache.py

# Or update specific components
python update_monthly_cache.py --prices-only
python update_monthly_cache.py --rainfall-only
python update_monthly_cache.py --ndvi-only
```

### Issue: Gradio App Not Loading

**Cause:** Missing dependencies or file paths

**Solution:**
```bash
# Check file structure
ls -la  # Should show: app.py, src/, production_model/, monthly_cache/

# Verify imports
python -c "import gradio; print('Gradio OK')"
python -c "import sys; sys.path.insert(0, 'src'); from src.inference import CropPricePredictor; print('Imports OK')"
```

### Issue: Large Repository Size

**Cause:** Git tracking large cache files

**Solution:**
Create `.gitattributes` in HF repo:
```gitattributes
*.json filter=lfs diff=lfs merge=lfs -text
*.csv filter=lfs diff=lfs merge=lfs -text
production_model/*.pkl filter=lfs diff=lfs merge=lfs -text
```

---

## 📈 Performance Expectations

With monthly cached data:

| Metric | Without Cache | With Cache |
|--------|--------------|------------|
| Prediction Time | 5-15 seconds | 0.2-0.5 seconds |
| API Calls | 3 per prediction | 0 |
| Success Rate | ~70% (API dependent) | ~98% |
| Cold Start | 10-20 seconds | 2-5 seconds |

---

## 🔒 Security Notes

1. **API Keys:** NOT needed for HF deployment (cache-only mode)
2. **Data Privacy:** All data is public agricultural market data
3. **Rate Limits:** Eliminated by using cache
4. **Dependencies:** Minimal attack surface (no external API calls)

---

## 📝 Maintenance Checklist

### Monthly (20-25th):
- [ ] Run `update_monthly_cache.py`
- [ ] Verify cache stats
- [ ] Test predictions locally
- [ ] Commit and push to HF
- [ ] Verify HF Space rebuilt successfully

### Quarterly:
- [ ] Review prediction accuracy
- [ ] Check for new crops/districts in data
- [ ] Update model if needed
- [ ] Validate cache cleanup (remove old entries)

### Annually:
- [ ] Retrain models with new year's data
- [ ] Update documentation
- [ ] Review system performance metrics

---

## 🎉 Success Criteria

Your deployment is successful when:

- ✅ Gradio app loads in HF Space
- ✅ All 45 crops selectable
- ✅ All 33 districts available
- ✅ Predictions return in < 1 second
- ✅ Cache status shows current data
- ✅ No API errors in logs

---

## 📞 Support

- **Issues:** https://github.com/YOUR_REPO/issues
- **Email:** your-email@example.com
- **HF Space:** https://huggingface.co/spaces/YOUR_USERNAME/crop-price-forecast

---

**Happy Deploying! 🚀🌾**
