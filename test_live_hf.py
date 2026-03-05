"""
Live HF API test: all valid crop-district combinations
Tests https://princegh410-crop-price.hf.space/api/predict
"""
import sys, os, time, json
sys.path.insert(0, 'src')

import pandas as pd
import urllib.request
import urllib.error

from src.config import DISTRICT_COORDS, normalize_district_name
from src.cached_fetcher import CachedDataFetcher
from src.inference import CropPricePredictor

API = "https://princegh410-crop-price.hf.space/api/predict"

# Build list of valid combos from local cache (same logic as local test)
predictor = CropPricePredictor(model_dir='production_model')
fetcher   = CachedDataFetcher(cache_dir='monthly_cache', use_api_fallback=False)

CROPS     = sorted(predictor.get_supported_crops())
DISTRICTS = sorted(DISTRICT_COORDS.keys())

# Collect valid combos
valid = []
for crop in CROPS:
    for district in DISTRICTS:
        price_data = fetcher.get_current_price(crop, district, 2026, 2)
        if price_data and price_data.get('monthly_mean_price', 0) > 0:
            crop_file = f"processed/{crop.lower().replace(' ', '_')}_final.csv"
            if os.path.exists(crop_file):
                df = pd.read_csv(crop_file)
                df['date'] = pd.to_datetime(df['date'])
                df['district_norm'] = df['district'].apply(normalize_district_name)
                hist = df[df['district_norm'] == district]
                if len(hist) >= 12:
                    valid.append((crop, district))

print(f"\n{'='*65}")
print(f"  LIVE HF API TEST — {len(valid)} valid combinations")
print(f"{'='*65}\n")

results = []
ok = fail = 0
t0 = time.time()

for i, (crop, district) in enumerate(valid):
    body = json.dumps({
        "commodity": crop,
        "district": district,
        "year": 2026,
        "month": 2
    }).encode()

    req = urllib.request.Request(
        API,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            pred = data.get("predicted_harvest_price", 0)
            ret  = data.get("expected_return_percent", 0)
            results.append({
                "crop": crop, "district": district, "status": "OK",
                "predicted": pred, "return_pct": ret, "error": ""
            })
            ok += 1
            # progress every 50
            if (i+1) % 50 == 0:
                elapsed = time.time() - t0
                print(f"  Progress: {i+1}/{len(valid)} done ({elapsed:.0f}s) — {ok} OK, {fail} FAIL")

    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        results.append({
            "crop": crop, "district": district, "status": "FAIL",
            "predicted": 0, "return_pct": 0, "error": f"HTTP {e.code}: {body_err[:200]}"
        })
        fail += 1
        print(f"  FAIL {crop} / {district} -> HTTP {e.code}: {body_err[:120]}")

    except Exception as e:
        results.append({
            "crop": crop, "district": district, "status": "FAIL",
            "predicted": 0, "return_pct": 0, "error": str(e)[:200]
        })
        fail += 1
        print(f"  FAIL {crop} / {district} -> {e}")

    time.sleep(0.05)  # be gentle on the API

elapsed = time.time() - t0

print(f"\n{'='*65}")
print(f"  LIVE HF RESULTS  ({elapsed:.0f}s)")
print(f"{'='*65}")
print(f"  ✓ OK   : {ok}")
print(f"  ✗ FAIL : {fail}")
print(f"{'='*65}\n")

df_out = pd.DataFrame(results)
df_out.to_csv("hf_live_test_results.csv", index=False)
print("  Saved: hf_live_test_results.csv\n")

if fail > 0:
    print("FAILURES:")
    for r in results:
        if r["status"] == "FAIL":
            print(f"  ✗  {r['crop']:<25} | {r['district']:<20} | {r['error'][:100]}")
else:
    print("ALL COMBINATIONS PASS ON LIVE HF API ✅")
