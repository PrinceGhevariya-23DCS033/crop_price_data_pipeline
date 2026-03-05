"""
Comprehensive test: all crops × all available districts
Tests the full prediction pipeline before HuggingFace upload.
"""
import sys, os, time
sys.path.insert(0, 'src')

import pandas as pd
from src.cached_fetcher import CachedDataFetcher
from src.inference import CropPricePredictor
from src.config import DISTRICT_COORDS, normalize_district_name

# ---- Init ----
predictor = CropPricePredictor(model_dir='production_model')
fetcher   = CachedDataFetcher(cache_dir='monthly_cache', use_api_fallback=False)

CROPS     = sorted(predictor.get_supported_crops())
DISTRICTS = sorted(DISTRICT_COORDS.keys())   # normalized lowercase names

print(f"\n{'='*65}")
print(f"  FULL PREDICTION TEST — {len(CROPS)} crops × {len(DISTRICTS)} districts")
print(f"{'='*65}\n")

results  = []
ok = fail = skip = 0
t0 = time.time()

for crop in CROPS:
    crop_file = f"processed/{crop.lower().replace(' ', '_')}_final.csv"
    if not os.path.exists(crop_file):
        for d in DISTRICTS:
            results.append({'crop': crop, 'district': d, 'status': 'SKIP', 'reason': 'no CSV file'})
        skip += len(DISTRICTS)
        continue

    df_full = pd.read_csv(crop_file)
    df_full['date'] = pd.to_datetime(df_full['date'])
    df_full['district_norm'] = df_full['district'].apply(normalize_district_name)

    for district in DISTRICTS:
        # --- cache check ---
        price_data = fetcher.get_current_price(crop, district, 2026, 2)
        if price_data is None or price_data.get('monthly_mean_price', 0) == 0:
            results.append({'crop': crop, 'district': district,
                            'status': 'SKIP', 'reason': 'no price cache'})
            skip += 1
            continue

        # --- historical data ---
        hist = df_full[df_full['district_norm'] == district].sort_values('date').tail(18).copy()
        if len(hist) < 12:
            results.append({'crop': crop, 'district': district,
                            'status': 'SKIP', 'reason': f'only {len(hist)} months history (need 12)'})
            skip += 1
            continue

        # --- prediction ---
        all_data = fetcher.get_all_data(crop, district, 2026, 2)
        try:
            result = predictor.predict(
                commodity=crop,
                district=district,
                current_price=all_data['current_price'],
                historical_data=hist,
                month=2,
                year=2026,
                monthly_rain_sum=all_data['monthly_rain_sum'],
                monthly_rain_mean=all_data['monthly_rain_mean'],
                monthly_ndvi_mean=all_data['monthly_ndvi_mean'],
                days_traded=all_data['days_traded']
            )
            results.append({
                'crop': crop, 'district': district, 'status': 'OK',
                'current_price': all_data['current_price'],
                'predicted_price': result['predicted_harvest_price'],
                'return_pct': result['expected_return_percent'],
                'reason': ''
            })
            ok += 1
        except Exception as e:
            results.append({'crop': crop, 'district': district,
                            'status': 'FAIL', 'reason': str(e)})
            fail += 1

elapsed = time.time() - t0

# ---- Summary ----
print(f"\n{'='*65}")
print(f"  RESULTS SUMMARY  ({elapsed:.1f}s)")
print(f"{'='*65}")
print(f"  ✓ OK   : {ok}")
print(f"  ✗ FAIL : {fail}")
print(f"  - SKIP : {skip}  (no cache data / insufficient history)")
print(f"{'='*65}\n")

# Show failures in detail
if fail > 0:
    print("FAILURES:")
    for r in results:
        if r['status'] == 'FAIL':
            print(f"  ✗  {r['crop']:25s} | {r['district']:20s} | {r['reason']}")
    print()

# Show OK summary (first 20, then count)
ok_rows = [r for r in results if r['status'] == 'OK']
print(f"SAMPLE SUCCESSES (first 20 of {len(ok_rows)}):")
print(f"  {'Crop':<25} {'District':<20} {'Current':>10} {'Predicted':>10} {'Return':>8}")
print(f"  {'-'*25} {'-'*20} {'-'*10} {'-'*10} {'-'*8}")
for r in ok_rows[:20]:
    print(f"  {r['crop']:<25} {r['district']:<20} "
          f"Rs{r['current_price']:>8.0f} Rs{r['predicted_price']:>8.0f} "
          f"{r['return_pct']:>+7.1f}%")

if ok == 0 and fail == 0:
    print("\n  ⚠  No predictions were tested (all skipped — cache may be empty).")

# Save full report to CSV
df_results = pd.DataFrame(results)
df_results.to_csv('test_results.csv', index=False)
print(f"\n  Full report saved to: test_results.csv")
print()
