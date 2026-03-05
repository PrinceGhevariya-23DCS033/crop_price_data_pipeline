# Quick Reference - GitHub Actions & Deployment
## Crop Price V2 System

---

## ⚡ Quick Commands

### Update NDVI Fallback (Run Monthly Before 20th)
```bash
# Generate fallback for current month
python update_ndvi_fallback.py

# Commit changes
git add NDVI/
git commit -m "Update NDVI fallback"
git push
```

### Local Testing
```bash
# Update cache locally
python update_monthly_cache.py

# Test Gradio app
python app.py
```

### Manual GitHub Action Trigger
1. Go to: **Actions → Monthly Cache Update → Run workflow**
2. Leave all options blank for current month
3. Click "Run workflow"

---

## 🔐 Required Secrets

Set these in **Settings → Secrets and variables → Actions**:

| Secret Name | Description | Get From |
|-------------|-------------|----------|
| `DATA_GOV_API_KEY` | data.gov.in API key | https://data.gov.in/user/register |
| `HF_TOKEN` | Hugging Face token | https://huggingface.co/settings/tokens |

---

## 📅 Monthly Workflow

| Date | Action | Command/Location |
|------|--------|------------------|
| **Before 20th** | Update NDVI fallback | `python update_ndvi_fallback.py` |
| **Before 20th** | Commit NDVI changes | `git add NDVI/ && git commit && git push` |
| **22nd (auto)** | GitHub Action runs | Check Actions tab |
| **After 22nd** | Verify deployment | Visit HF Space URL |

---

## 🎯 Deployment Modes

### Cache-Only Update (Default)
**Use for:** Monthly updates
**Uploads:** Only `monthly_cache/` directory (~1-5 MB)
**Time:** ~30 seconds
```
Force deploy: false
```

### Full Deployment
**Use for:** Initial setup, major changes
**Uploads:** All files including models (~50-500 MB)
**Time:** ~2-10 minutes
```
Force deploy: true
```

---

## 📂 Files That Get Uploaded

### Always Uploaded (Cache-Only)
```
monthly_cache/
├── prices/*.json         # Commodity-district prices
├── rainfall/*.json       # District rainfall data
├── ndvi/*.json          # District NDVI values
└── cache_metadata.json  # Update timestamp & stats
```

### Uploaded on Force Deploy
```
app.py                    # Gradio application
src/                      # Python source code
district_latlon.csv       # District coordinates
requirements.txt          # Dependencies
production_model/         # Trained models (large)
processed/               # Historical data (large)
```

---

## 🛰️ NDVI Update Options

### Option 1: Fallback Script (Easiest)
```bash
python update_ndvi_fallback.py --year 2026 --month 3
```
✅ No authentication needed
✅ Uses historical patterns
⚠️ Approximate values

### Option 2: Google Earth Engine (Most Accurate)
```bash
earthengine authenticate
# Then export NDVI data manually
```
✅ Real satellite data
⚠️ Requires authentication
⚠️ Complex setup

### Option 3: Use Latest Available (No Action)
✅ Automatic fallback
⚠️ May use old data

---

## 🔍 Troubleshooting Quick Fixes

| Error | Quick Fix |
|-------|-----------|
| "HF_TOKEN not set" | Add secret in Settings → Secrets |
| "Only X price files" | Re-run workflow or use `skip_prices: true` |
| "No NDVI data" | Run `update_ndvi_fallback.py` locally & push |
| "Upload failed" | Check HF_SPACE_ID in `ci_upload_to_hf.py` |
| Workflow fails | Check Actions logs for details |

---

## 📊 Check Deployment Status

### GitHub Actions
```
Repository → Actions → Latest workflow run → View logs
```

### Hugging Face Space
```
https://huggingface.co/spaces/princegh410/crop-price
Click "View logs" to see build status
```

### Cache Statistics
```bash
python -c "
import sys; sys.path.insert(0, 'src')
from src.monthly_cache import MonthlyDataCache
print(MonthlyDataCache().get_cache_stats())
"
```

---

## 🔗 Important URLs

| Resource | URL |
|----------|-----|
| Your HF Space | https://huggingface.co/spaces/princegh410/crop-price |
| GitHub Actions | (Your repo) → Actions |
| HF Tokens | https://huggingface.co/settings/tokens |
| data.gov.in | https://data.gov.in/ |

---

## 📝 Workflow Inputs Cheat Sheet

### Manual Trigger Options:

| Input | Values | Purpose |
|-------|--------|---------|
| **Year** | blank or 2026 | Which year to update |
| **Month** | blank or 1-12 | Which month to update |
| **Skip prices?** | false (default) / true | Skip data.gov.in API |
| **Force deploy?** | false (default) / true | Upload all files |

### Example Scenarios:

**Regular monthly update:**
```
Year: (blank)       Month: (blank)
Skip prices: false  Force deploy: false
```

**Update specific month:**
```
Year: 2026          Month: 3
Skip prices: false  Force deploy: false
```

**Test without API calls:**
```
Year: (blank)       Month: (blank)
Skip prices: true   Force deploy: false
```

**Full redeployment:**
```
Year: (blank)       Month: (blank)
Skip prices: false  Force deploy: true
```

---

## ⏰ Automatic Schedule

**Cron:** `0 2 22 * *`  
**Meaning:** 02:00 UTC on the 22nd of every month  
**Your timezone:** Calculate from UTC

---

## 💡 Pro Tips

1. **Always test locally first:**
   ```bash
   python update_monthly_cache.py
   python app.py
   ```

2. **Monitor workflow runs** in Actions tab

3. **Update NDVI before** automatic run (before 22nd)

4. **Use cache-only mode** for monthly updates to save time

5. **Full deploy only when needed** (code changes, model updates)

6. **Check HF Space logs** after deployment

---

**For detailed information, see:** [GITHUB_ACTIONS_GUIDE.md](GITHUB_ACTIONS_GUIDE.md)
