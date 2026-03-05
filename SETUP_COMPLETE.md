# 🎉 GitHub Actions & Deployment Setup - COMPLETE

## ✅ What Has Been Done

I've improved your GitHub Actions workflow and created a complete solution for automated deployment to Hugging Face. Here's what's new:

---

## 📦 New/Updated Files

### 1. **`.github/workflows/monthly-cache-update.yml`** (Updated)
**Changes:**
- ✅ Added fallback error handling for failed cache updates
- ✅ Added NDVI data availability checking
- ✅ New option: `force_deploy` for full deployment vs cache-only
- ✅ Better file preparation with staging directory
- ✅ Enhanced verification and summary reports
- ✅ Improved error messages and warnings

### 2. **`ci_upload_to_hf.py`** (Updated)
**Changes:**
- ✅ Two modes: cache-only (default) or full deployment
- ✅ Smarter file selection based on deployment mode
- ✅ File size checking and reporting
- ✅ Better error handling and progress reporting
- ✅ Uploads only necessary files for each mode

### 3. **`update_ndvi_fallback.py`** (New)
**Purpose:** Generate fallback NDVI values when Google Earth Engine is not available

**Features:**
- ✅ Uses historical data from previous years
- ✅ Applies seasonal variation (±5%)
- ✅ Automatically backs up before modifying CSV
- ✅ Preview mode to check before saving
- ✅ Supports custom year/month selection

**Usage:**
```bash
# Generate fallback for current month
python update_ndvi_fallback.py

# Generate for specific month
python update_ndvi_fallback.py --year 2026 --month 3

# Preview without saving
python update_ndvi_fallback.py --preview
```

### 4. **`GITHUB_ACTIONS_GUIDE.md`** (New)
Complete guide covering:
- GitHub Actions setup and configuration
- Required secrets (DATA_GOV_API_KEY, HF_TOKEN)
- How to trigger workflows manually
- NDVI update strategies (3 options)
- Troubleshooting common issues
- Recommended monthly workflow
- Files uploaded to Hugging Face

### 5. **`QUICK_REFERENCE_GITHUB_ACTIONS.md`** (New)
Quick reference card with:
- Essential commands
- Deployment modes comparison
- Monthly workflow checklist
- Troubleshooting quick fixes
- Workflow inputs cheat sheet

### 6. **`.gitignore`** (Updated)
Added exclusions for:
- NDVI backup files (`*_backup.csv`)
- GitHub Actions staging directory (`hf_deploy/`)

---

## 🔐 Setup Required (Action Items)

### 1. Configure GitHub Secrets

Go to your repository: **Settings → Secrets and variables → Actions → New repository secret**

Add these two secrets:

| Secret Name | How to Get It | Purpose |
|-------------|---------------|---------|
| `DATA_GOV_API_KEY` | Register at [data.gov.in](https://data.gov.in/user/register) | Fetch mandi prices |
| `HF_TOKEN` | Get from [HF Settings](https://huggingface.co/settings/tokens) | Deploy to HF Space |

**Important:** HF_TOKEN needs **write** permission!

### 2. Create Hugging Face Space (If Not Already Done)

1. Go to https://huggingface.co/new-space
2. Fill in:
   - **Name:** `crop-price` (or your choice)
   - **SDK:** Gradio
   - **Hardware:** CPU Basic (free tier)
   - **Visibility:** Public or Private
3. Click "Create Space"

### 3. Update HF_SPACE_ID

Edit [`ci_upload_to_hf.py`](ci_upload_to_hf.py) line 15:

```python
HF_SPACE_ID = "YOUR_USERNAME/crop-price"  # Change to your actual username
```

Replace `YOUR_USERNAME` with your actual Hugging Face username.

### 4. Commit All Changes

```bash
# Add all new files
git add .github/workflows/monthly-cache-update.yml
git add ci_upload_to_hf.py
git add update_ndvi_fallback.py
git add GITHUB_ACTIONS_GUIDE.md
git add QUICK_REFERENCE_GITHUB_ACTIONS.md
git add .gitignore

# Commit
git commit -m "Add GitHub Actions workflow and NDVI fallback support"

# Push to GitHub
git push
```

---

## 🛰️ NDVI Data Solution

### The Problem
- Your NDVI CSV only has data up to 2024
- We're in 2026 now
- Google Earth Engine requires complex authentication in GitHub Actions

### The Solution
Use the **fallback script** to generate NDVI values:

```bash
# Generate fallback NDVI for current month
python update_ndvi_fallback.py
```

**How it works:**
1. Reads historical NDVI from the CSV
2. Uses the same month from previous years
3. Applies slight variation (±5%) for realism
4. Updates the CSV with new data
5. Creates automatic backup

**Run this monthly** (before the 22nd) to keep NDVI data current!

---

## 📅 Monthly Workflow (Recommended)

### Before 20th of Each Month:

**Step 1:** Update NDVI fallback
```bash
cd Crop_Price_V2
python update_ndvi_fallback.py
```

**Step 2:** Commit changes
```bash
git add NDVI/
git commit -m "Update NDVI fallback for $(date +'%Y-%m')"
git push
```

### On 22nd (Automatic):

✅ GitHub Action runs automatically  
✅ Fetches latest prices from data.gov.in  
✅ Fetches rainfall from Open-Meteo  
✅ Uses NDVI from your updated CSV  
✅ Uploads to Hugging Face  

**No action needed!** Just monitor in Actions tab.

### After 22nd:

**Check status:**
1. Go to **Actions** tab
2. View latest workflow run
3. Check the summary

**Verify deployment:**
1. Visit your Hugging Face Space
2. Test a few predictions
3. Check cache status tab

---

## 🎯 How to Use GitHub Actions

### Automatic Runs

The workflow runs **automatically on the 22nd** of every month at 02:00 UTC.

**Schedule:** `0 2 22 * *`

### Manual Runs

**When to use:**
- Test before the automatic run
- Update a past month
- Force redeployment

**How to trigger:**

1. Go to **Actions** tab in your repository
2. Click **"Monthly Cache Update to Hugging Face"**
3. Click **"Run workflow"** button (top right)
4. Fill in options (or leave blank for defaults):
   - **Year:** Leave blank for current year
   - **Month:** Leave blank for current month
   - **Skip prices?** false (default) or true
   - **Force deploy?** false (default) or true
5. Click **"Run workflow"**

### Deployment Modes

**Cache-Only (Default):**
- `force_deploy: false`
- Uploads only `monthly_cache/` (~1-5 MB)
- Fast (~30 seconds)
- Use for monthly updates

**Full Deployment:**
- `force_deploy: true`
- Uploads everything including models (~50-500 MB)
- Slower (~2-10 minutes)
- Use for initial setup or major changes

---

## 📂 What Gets Uploaded

### Every Update (Cache-Only Mode)
```
monthly_cache/
├── prices/
│   └── [commodity]_[district].json  (1,485 files)
├── rainfall/
│   └── [district].json              (33 files)
├── ndvi/
│   └── [district].json              (33 files)
└── cache_metadata.json
```

### Full Deployment Only
```
app.py                     # Gradio app
src/                       # All Python code
district_latlon.csv        # District coordinates
requirements.txt           # Dependencies
production_model/          # ML models (optional, if force mode)
processed/                 # Historical CSVs (optional, if force mode)
```

---

## 🔍 Monitoring & Logs

### GitHub Actions Logs
```
Your Repository → Actions → Select workflow run → View logs
```

Shows:
- Cache update progress
- Number of files generated
- Upload status
- Any errors

### Hugging Face Space Logs
```
https://huggingface.co/spaces/YOUR_USERNAME/crop-price
→ Click "View logs" or "Building" status
```

Shows:
- Build progress
- Dependency installation
- App startup
- Runtime errors

---

## ⚠️ Common Issues & Solutions

### Issue: "HF_TOKEN environment variable not set"
**Solution:** Add HF_TOKEN secret in Settings → Secrets

### Issue: "Only X price files generated"
**Cause:** data.gov.in API issue or rate limit  
**Solution:** 
- Check DATA_GOV_API_KEY is valid
- Wait and retry
- Or run with `skip_prices: true`

### Issue: "No NDVI data available"
**Cause:** CSV doesn't have current month  
**Solution:** Run `update_ndvi_fallback.py` locally and push

### Issue: "Upload failed"
**Cause:** Wrong HF_SPACE_ID or token lacks permission  
**Solution:** 
- Verify HF_SPACE_ID in `ci_upload_to_hf.py`
- Ensure HF token has write access

---

## 🧪 Testing

### Test Locally First

```bash
# 1. Update cache
python update_monthly_cache.py

# 2. Test Gradio app
python app.py

# 3. Open in browser
# http://localhost:7860
```

### Test GitHub Action

```bash
# Trigger manually with test options
Actions → Run workflow
Year: (blank)
Month: (blank)
Skip prices: true      # Don't waste API calls
Force deploy: false
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [`GITHUB_ACTIONS_GUIDE.md`](GITHUB_ACTIONS_GUIDE.md) | Complete guide with detailed explanations |
| [`QUICK_REFERENCE_GITHUB_ACTIONS.md`](QUICK_REFERENCE_GITHUB_ACTIONS.md) | Quick commands and cheat sheet |
| This file | Setup summary and action items |

---

## ✨ Key Benefits

✅ **Automatic monthly updates** - Set it and forget it  
✅ **No manual deployment** - Push to HF automatically  
✅ **NDVI fallback** - Works without Google Earth Engine  
✅ **Robust error handling** - Graceful failures  
✅ **Two deployment modes** - Cache-only or full  
✅ **Detailed logging** - Easy troubleshooting  
✅ **Manual override** - Test anytime  

---

## 🚀 Next Steps

1. ✅ **Configure GitHub secrets** (DATA_GOV_API_KEY, HF_TOKEN)
2. ✅ **Update HF_SPACE_ID** in `ci_upload_to_hf.py`
3. ✅ **Commit and push** all changes
4. ✅ **Run fallback script** for current month: `python update_ndvi_fallback.py`
5. ✅ **Commit NDVI update** and push
6. ✅ **Test manually** via Actions → Run workflow
7. ✅ **Verify deployment** on Hugging Face Space

---

## 📞 Need Help?

**Check these files:**
- [`GITHUB_ACTIONS_GUIDE.md`](GITHUB_ACTIONS_GUIDE.md) - Detailed troubleshooting
- [`QUICK_REFERENCE_GITHUB_ACTIONS.md`](QUICK_REFERENCE_GITHUB_ACTIONS.md) - Quick fixes

**Check logs:**
- GitHub: Actions tab → Latest run
- Hugging Face: Your space → View logs

---

**Setup completed!** 🎉

Your crop price forecasting system now has:
- ✅ Automated monthly deployment
- ✅ NDVI fallback support
- ✅ Robust error handling
- ✅ Complete documentation

**Everything is ready to go!** Just complete the setup steps above and you're done.
