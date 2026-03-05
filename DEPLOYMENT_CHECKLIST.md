# Hugging Face Deployment Checklist
# Gujarat Crop Price Forecasting System

Use this checklist to ensure smooth deployment to Hugging Face Spaces.

---

## 📋 Pre-Deployment Checklist

### 1. ✅ Data Preparation

- [ ] **Run monthly cache update**
  ```bash
  python update_monthly_cache.py
  ```

- [ ] **Verify cache is populated**
  ```bash
  python -c "import sys; sys.path.insert(0, 'src'); from src.monthly_cache import MonthlyDataCache; stats = MonthlyDataCache().get_cache_stats(); print(f'Prices: {stats[\"total_price_entries\"]}\nRainfall: {stats[\"total_rainfall_entries\"]}\nNDVI: {stats[\"total_ndvi_entries\"]}')"
  ```
  - Expected: ~1485 prices, 33 rainfall, 33 NDVI

- [ ] **Check cache is current**
  - Last update should be within current month
  - Update date should be after 20th

### 2. ✅ Files Ready

Check these files exist:

- [ ] `app.py` (Gradio app)
- [ ] `requirements_hf.txt` (Will rename to requirements.txt)
- [ ] `README_HF.md` (Will rename to README.md)
- [ ] `src/` directory with all modules:
  - [ ] `src/inference.py`
  - [ ] `src/cached_fetcher.py`
  - [ ] `src/monthly_cache.py`
  - [ ] `src/data_fetchers.py`
  - [ ] `src/config.py`
  - [ ] `src/__init__.py`
- [ ] `production_model/` directory with model files
- [ ] `processed/` directory with CSV files
- [ ] `monthly_cache/` directory with cached data
- [ ] `district_latlon.csv`

### 3. ✅ Local Testing

- [ ] **Test Gradio app locally**
  ```bash
  python app.py
  ```
  - App should open at http://localhost:7860

- [ ] **Test predictions**
  - Try Wheat + Ahmedabad
  - Try Cotton + Rajkot
  - Try Onion + Anand
  - All should return predictions in <1 second

- [ ] **Check cache status tab**
  - Should show current cache info

- [ ] **Verify no errors in console**

### 4. ✅ Repository Cleanup

- [ ] Remove unnecessary files (tests, notebooks, etc.)
- [ ] Verify .gitignore_hf covers what to exclude
- [ ] Check file sizes (HF has 50GB limit)
  ```bash
  du -sh monthly_cache/
  du -sh production_model/
  du -sh processed/
  ```

---

## 🚀 Deployment Steps

### Option A: Web Interface Deployment

1. [ ] **Create Hugging Face Space**
   - Go to https://huggingface.co/new-space
   - Name: `crop-price-forecast` (or your choice)
   - SDK: Gradio
   - Hardware: CPU Basic (free)
   - Visibility: Public or Private

2. [ ] **Upload Files**
   - Upload all files from checklist above
   - Rename `requirements_hf.txt` → `requirements.txt`
   - Rename `README_HF.md` → `README.md`

3. [ ] **Wait for Build**
   - HF will automatically install deps and start app
   - Check build logs for errors
   - Usually takes 2-5 minutes

4. [ ] **Test Deployed App**
   - Open your Space URL
   - Test 3-4 predictions
   - Check cache status

### Option B: Git Deployment (Recommended)

1. [ ] **Clone HF Space repo**
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/crop-price-forecast
   cd crop-price-forecast
   ```

2. [ ] **Copy files**
   ```bash
   # From Crop_Price_V2 directory
   cp app.py ../crop-price-forecast/
   cp requirements_hf.txt ../crop-price-forecast/requirements.txt
   cp README_HF.md ../crop-price-forecast/README.md
   cp district_latlon.csv ../crop-price-forecast/
   cp -r src/ ../crop-price-forecast/
   cp -r production_model/ ../crop-price-forecast/
   cp -r processed/ ../crop-price-forecast/
   cp -r monthly_cache/ ../crop-price-forecast/
   ```

3. [ ] **Setup Git LFS (for large files)**
   ```bash
   cd ../crop-price-forecast
   git lfs install
   git lfs track "*.pkl"
   git lfs track "*.csv"
   git lfs track "*.json"
   git add .gitattributes
   ```

4. [ ] **Commit and push**
   ```bash
   git add .
   git commit -m "Initial deployment with cached data"
   git push
   ```

5. [ ] **Verify deployment**
   - Wait for HF to rebuild (2-5 min)
   - Check build logs
   - Test app

---

## 🧪 Post-Deployment Verification

### Functionality Tests

- [ ] **App loads successfully**
  - No build errors
  - Gradio interface visible

- [ ] **All dropdowns populated**
  - 45 crops visible
  - 33 districts visible

- [ ] **Predictions work**
  - Test 5 random crop-district combinations
  - All return results in <1 second
  - No "data not available" errors for major crops

- [ ] **Cache status accurate**
  - Shows recent update date
  - Entry counts match local cache

### Performance Tests

- [ ] **Cold start time** < 10 seconds
- [ ] **Prediction time** < 1 second
- [ ] **No API timeouts** (since using cache)
- [ ] **No 503 errors** (model loads properly)

### UI/UX Tests

- [ ] Text renders properly
- [ ] Markdown formatting correct
- [ ] Examples in tabs work
- [ ] No broken links

---

## 🐛 Troubleshooting Guide

### Build Fails

**Error:** "No module named 'src'"
```bash
# Fix: Ensure src/ directory is uploaded
# Check app.py has: sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
```

**Error:** "Could not find production_model"
```bash
# Fix: Ensure production_model/ directory is uploaded
# Check it contains model pickle files
```

**Error:** "Requirements installation failed"
```bash
# Fix: Check requirements_hf.txt has correct package names
# Remove version constraints that might conflict
```

### App Loads But Predictions Fail

**Error:** "No Price Data Available"
```bash
# Fix: Verify monthly_cache/ is uploaded
# Check cache has files: ls monthly_cache/prices/
```

**Error:** "Model not loaded"
```bash
# Fix: Check production_model/ contains .pkl files
# Verify src/inference.py can import model
```

### Slow Performance

**Issue:** Predictions take >3 seconds
```bash
# Check: Are API fallbacks enabled?
# Fix: In cached_fetcher.py, ensure use_api_fallback=False
```

**Issue:** App doesn't start
```bash
# Check build logs for errors
# Verify all dependencies in requirements.txt
# Check Gradio version compatibility
```

---

## 📊 Success Metrics

Your deployment is successful when:

| Metric | Target | Status |
|--------|--------|--------|
| Build time | < 5 minutes | [ ] |
| Cold start | < 10 seconds | [ ] |
| Prediction time | < 1 second | [ ] |
| Success rate | > 95% | [ ] |
| Cache entries | 1485+ prices | [ ] |
| Uptime | > 99% | [ ] |

---

## 🔄 Monthly Maintenance

After each monthly update:

1. [ ] Run `update_monthly_cache.py` locally (20-25th)
2. [ ] Verify cache updated successfully
3. [ ] Test locally
4. [ ] Commit updated cache to HF repo
5. [ ] Push to HF
6. [ ] Verify HF rebuilt successfully
7. [ ] Test predictions on HF
8. [ ] Update log in `cache_update_log.txt`

---

## 📝 Deployment Log

Track your deployments:

```
Date       | Action           | Status | Notes
-----------|------------------|--------|---------------------------
2024-02-20 | Initial deploy   | ✅     | Cache for Feb, all working
2024-03-22 | Cache update     | ✅     | March data, no issues
2024-04-20 | Cache update     | ⚠️     | Some API timeouts, used CSV fallback
```

---

## 🎉 Ready to Deploy?

Final checklist:

- [ ] All pre-deployment items completed
- [ ] Local testing passed
- [ ] Files prepared and organized
- [ ] Git LFS configured (if using git)
- [ ] HF Space created
- [ ] Ready to push!

**If all checked, proceed with deployment! 🚀**

---

## 📞 Need Help?

- HF Docs: https://huggingface.co/docs/hub/spaces
- Gradio Docs: https://gradio.app/docs
- Project Issues: [Your GitHub repo]
- Email: your-email@example.com

---

**Good luck with your deployment! 🌾✨**
