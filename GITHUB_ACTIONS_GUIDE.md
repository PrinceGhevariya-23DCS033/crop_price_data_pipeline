# GitHub Actions & NDVI Update Guide
## Gujarat Crop Price Forecasting System

This guide explains how to use the GitHub Actions workflow and handle NDVI data updates.

---

## 📋 Overview

The system uses a GitHub Action to automatically:
1. **Update monthly cache** (prices, rainfall, NDVI)
2. **Upload to Hugging Face Space** for deployment
3. Runs **automatically on the 22nd** of each month
4. Can be **triggered manually** for testing or updates

---

## 🚀 GitHub Action Setup

### Prerequisites

1. **GitHub Repository Secrets** (Settings → Secrets and variables → Actions)
   
   Add these secrets:
   - `DATA_GOV_API_KEY` - Your data.gov.in API key (for mandi prices)
   - `HF_TOKEN` - Your Hugging Face token (for deployment)
     - Get it from: https://huggingface.co/settings/tokens
     - Needs `write` permission

2. **Hugging Face Space**
   - Create a Space at https://huggingface.co/new-space
   - Name: `crop-price` (or your choice)
   - SDK: Gradio
   - Hardware: CPU Basic (free tier works)

### Workflow File

The workflow is located at: `.github/workflows/monthly-cache-update.yml`

**Key Features:**
- ✅ Automatic monthly updates (22nd of every month)
- ✅ Manual trigger with custom parameters
- ✅ Handles NDVI data fallback when not available
- ✅ Robust error handling
- ✅ Two deployment modes: cache-only or full deployment

---

## 🎯 How to Use

### Automatic Monthly Updates

The workflow runs automatically on the **22nd of every month at 02:00 UTC**.

It will:
1. Fetch latest mandi prices (last 30 days average)
2. Fetch rainfall data (previous month)
3. Use NDVI data from CSV (with fallback if needed)
4. Upload monthly_cache/ to Hugging Face

**No action required!** Just check the Actions tab for status.

### Manual Trigger

Go to **Actions** → **Monthly Cache Update to Hugging Face** → **Run workflow**

#### Options:

1. **Year** (optional)
   - Leave blank for current year
   - Or specify a year (e.g., 2026)

2. **Month** (optional)
   - Leave blank for current month
   - Or specify 1-12

3. **Skip price update?**
   - `false` (default): Fetch new prices from data.gov.in
   - `true`: Skip price update, only update rainfall/NDVI

4. **Force full deployment?**
   - `false` (default): Only upload monthly_cache/
   - `true`: Upload all files (app.py, src/, models, etc.)

#### Example Usage:

**Update cache for March 2026:**
```
Year: 2026
Month: 3
Skip prices: false
Force deploy: false
```

**Test deployment without fetching new data:**
```
Year: (blank - current)
Month: (blank - current)
Skip prices: true
Force deploy: false
```

**Full redeployment with all files:**
```
Year: (blank)
Month: (blank)
Skip prices: false
Force deploy: true
```

---

## 🛰️ NDVI Data Updates

### The NDVI Challenge

**Problem:** NDVI data comes from satellite imagery, which requires:
- Google Earth Engine authentication (difficult in GitHub Actions)
- API credentials and tokens
- Complex setup

**Solution:** We use a CSV-based approach with fallback mechanisms.

### Current NDVI Data

The NDVI CSV file is located at:
```
NDVI/gujarat_monthly_ndvi_clean_2005_2024_final.csv
```

This contains historical NDVI data from 2005-2024.

### For Months Beyond 2024

Since the CSV only has data up to 2024, we have **three options**:

---

#### Option 1: Use Fallback Script (Recommended)

Generate fallback NDVI values based on historical data:

```bash
# Generate fallback for current month
python update_ndvi_fallback.py

# Generate for specific month
python update_ndvi_fallback.py --year 2026 --month 3

# Preview without saving
python update_ndvi_fallback.py --year 2026 --month 3 --preview
```

**How it works:**
- Uses same month from previous years
- Applies slight seasonal variation (±5%)
- Ensures valid NDVI range (0.0 - 1.0)
- Creates backup before modifying CSV

**When to run:**
- Run locally before the 22nd of each month
- Commit the updated NDVI CSV to your repository
- GitHub Action will use the updated data

---

#### Option 2: Manual NDVI Update

If you have access to Google Earth Engine:

1. **Authenticate with GEE:**
   ```bash
   pip install earthengine-api
   earthengine authenticate
   ```

2. **Export NDVI data** for your districts and dates

3. **Update the CSV file:**
   ```python
   import pandas as pd
   
   # Load existing data
   df = pd.read_csv('NDVI/gujarat_monthly_ndvi_clean_2005_2024_final.csv')
   
   # Add new rows with your NDVI data
   new_data = pd.DataFrame([
       {'district': 'Ahmedabad', 'date': '2026-03-01', 'monthly_ndvi_mean': 0.65},
       {'district': 'Rajkot', 'date': '2026-03-01', 'monthly_ndvi_mean': 0.58},
       # ... add all districts
   ])
   
   df = pd.concat([df, new_data], ignore_index=True)
   df.to_csv('NDVI/gujarat_monthly_ndvi_clean_2005_2024_final.csv', index=False)
   ```

4. **Commit and push** the updated CSV

---

#### Option 3: Use Latest Available NDVI

The system automatically falls back to the most recent NDVI value for each district.

**No action required** - the system handles this automatically in `src/data_fetchers.py`:

```python
def get_ndvi_from_csv(self, commodity, district, year, month):
    # Loads CSV and gets latest NDVI for the district
    # If exact month not found, uses most recent available
```

**Pros:**
- Zero maintenance
- Works automatically

**Cons:**
- Uses outdated NDVI values
- May reduce prediction accuracy slightly

---

## 📊 Monitoring & Troubleshooting

### Check Workflow Status

1. Go to **Actions** tab in your GitHub repository
2. Click on the latest workflow run
3. Check each step for errors

### View Deployment Summary

Each workflow run creates a summary showing:
- Number of price files updated
- Number of rainfall files updated
- Number of NDVI files updated
- Deployment status
- Hugging Face Space URL

### Common Issues

#### ❌ "Only X price files generated"

**Cause:** data.gov.in API failed or rate limited

**Solution:**
- Check your `DATA_GOV_API_KEY` secret is valid
- Wait a few hours and try again
- Run manually with `skip_prices: true` to update only rainfall/NDVI

#### ❌ "No NDVI data available"

**Cause:** NDVI CSV doesn't have data for the requested month

**Solution:**
- Run `update_ndvi_fallback.py` locally
- Commit updated CSV
- Re-run the workflow

#### ❌ "HF_TOKEN environment variable not set"

**Cause:** Hugging Face token not configured

**Solution:**
- Go to Settings → Secrets → Actions
- Add secret `HF_TOKEN` with your HF token
- Token needs `write` permission

#### ❌ "Upload failed: Repository not found"

**Cause:** Hugging Face Space ID incorrect or token lacks permission

**Solution:**
- Check `HF_SPACE_ID` in `ci_upload_to_hf.py` matches your space
- Format: `username/space-name` (all lowercase)
- Ensure HF token has access to the space

---

## 🔄 Recommended Monthly Workflow

**Before 20th of month:**
```bash
# 1. Generate fallback NDVI for current month
python update_ndvi_fallback.py

# 2. Review and commit
git add NDVI/
git commit -m "Update NDVI fallback for $(date +'%Y-%m')"
git push
```

**On 22nd (automatic):**
- GitHub Action runs automatically
- Fetches latest prices and rainfall
- Uses NDVI from CSV (with your fallbacks)
- Deploys to Hugging Face

**After 22nd:**
- Check Actions tab for status
- Verify Hugging Face Space is updated
- Test predictions on your Space

---

## 📁 Files Uploaded to Hugging Face

### Cache-Only Mode (Default)

Only uploads:
- `monthly_cache/prices/*.json` (commodity-district prices)
- `monthly_cache/rainfall/*.json` (district rainfall)
- `monthly_cache/ndvi/*.json` (district NDVI)
- `monthly_cache/cache_metadata.json` (metadata)

**Size:** ~1-5 MB
**Upload time:** ~30 seconds

### Full Deployment Mode

Uploads everything:
- All cache files (above)
- `app.py` (Gradio application)
- `src/` (Python source code)
- `district_latlon.csv` (district coordinates)
- `requirements.txt` (dependencies)
- `production_model/` (trained models) *if force mode*
- `processed/` (historical CSVs) *if force mode*

**Size:** ~50-500 MB (depends on models)
**Upload time:** ~2-10 minutes

---

## 🎓 Tips & Best Practices

1. **Test locally first**
   ```bash
   python update_monthly_cache.py
   python app.py  # Test Gradio app
   ```

2. **Use manual trigger for testing**
   - Try `skip_prices: true` first to save API calls
   - Test with past months to verify behavior

3. **Monitor API usage**
   - data.gov.in has rate limits
   - Don't run the workflow too frequently

4. **Keep NDVI CSV updated**
   - Run fallback script before month end
   - Commit changes to repository

5. **Full deployment only when needed**
   - Use `force_deploy: false` for monthly updates
   - Use `force_deploy: true` only for:
     - Initial deployment
     - Major code changes
     - Model updates

6. **Check Hugging Face Space logs**
   - Click "View logs" on your Space
   - Check for build errors
   - Verify cache files are loaded

---

## 🔗 Useful Links

- **GitHub Actions Documentation:** https://docs.github.com/en/actions
- **Hugging Face Spaces:** https://huggingface.co/docs/hub/spaces
- **data.gov.in API:** https://data.gov.in/
- **Google Earth Engine:** https://earthengine.google.com/

---

## 📞 Support

If you encounter issues:

1. Check the workflow logs in GitHub Actions
2. Review the Hugging Face Space build logs
3. Verify all secrets are configured correctly
4. Test locally with the same data

For NDVI-specific issues:
- Verify CSV file exists and has data
- Check date format in CSV matches `YYYY-MM-DD`
- Ensure district names match those in `src/config.py`

---

**Last Updated:** March 2026
