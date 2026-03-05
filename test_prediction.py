"""
Test the complete prediction pipeline with feature engineering
"""

import sys
import os
sys.path.insert(0, 'src')

from inference import CropPricePredictor
from data_fetchers import MandiPriceFetcher, WeatherFetcher, NDVIFetcher
from datetime import datetime
import pandas as pd

print("=" * 80)
print("TESTING PREDICTION PIPELINE WITH FEATURE ENGINEERING")
print("=" * 80)

# Initialize components
print("\nInitializing components...")
try:
    predictor = CropPricePredictor(model_dir="production_model")
    mandi = MandiPriceFetcher()
    weather = WeatherFetcher()
    ndvi = NDVIFetcher()
    print("✓ All components initialized\n")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test prediction
test_cases = [
    ("Onion", "Rajkot", 2024, 1),
    ("Wheat", "Vadodara", 2023, 12),
]

for commodity, district, year, month in test_cases:
    print("=" * 80)
    print(f"Testing: {commodity} in {district} ({year}-{month:02d})")
    print("=" * 80)
    
    try:
        # Step 1: Get historical data
        print("\n[1/4] Loading historical data...")
        historical_data = mandi.fetch_historical_monthly_prices(
            commodity=commodity,
            district=district,
            months_back=18
        )
        
        if historical_data.empty:
            print(f"  ❌ No historical data found")
            continue
        
        print(f"  ✓ Loaded {len(historical_data)} months of data")
        
        # Ensure required columns
        if "monthly_rain_sum" not in historical_data.columns:
            historical_data["monthly_rain_sum"] = 0.0
        if "monthly_rain_mean" not in historical_data.columns:
            historical_data["monthly_rain_mean"] = 0.0
        if "monthly_ndvi_mean" not in historical_data.columns:
            historical_data["monthly_ndvi_mean"] = 0.5
        
        # Step 2: Get current price
        print("\n[2/4] Getting current price...")
        current_price_data = mandi.get_current_price_with_fallback(
            commodity=commodity,
            district=district,
            reference_date=datetime(year, month, 15)
        )
        
        if not current_price_data:
            print(f"  ❌ No current price data")
            continue
        
        print(f"  ✓ {current_price_data['price_source']}")
        print(f"  ✓ Price: ₹{current_price_data['monthly_mean_price']:.2f}")
        
        # Step 3: Get weather/NDVI
        print("\n[3/4] Getting weather and NDVI...")
        weather_data = weather.get_monthly_rainfall(district, year, month)
        ndvi_data = ndvi.get_monthly_ndvi(district, year, month)
        
        rain_sum = weather_data.get("monthly_rain_sum", 0) if weather_data else 0
        rain_mean = weather_data.get("monthly_rain_mean", 0) if weather_data else 0
        ndvi_mean = ndvi_data.get("monthly_ndvi_mean", 0.5) if ndvi_data else 0.5
        
        print(f"  ✓ Rain: {rain_sum:.1f}mm")
        print(f"  ✓ NDVI: {ndvi_mean:.3f}")
        
        # Step 4: Make prediction
        print("\n[4/4] Making prediction...")
        
        from config import normalize_district_name
        normalized_district = normalize_district_name(district)
        
        result = predictor.predict(
            commodity=commodity,
            district=normalized_district,
            current_price=current_price_data["monthly_mean_price"],
            historical_data=historical_data,
            month=month,
            year=year,
            monthly_rain_sum=rain_sum,
            monthly_rain_mean=rain_mean,
            monthly_ndvi_mean=ndvi_mean,
            days_traded=current_price_data.get("days_traded", 20)
        )
        
        print(f"\n✅ PREDICTION SUCCESS!")
        print(f"  Current Price: ₹{result['current_price']:.2f}")
        print(f"  Predicted Harvest Price: ₹{result['predicted_harvest_price']:.2f}")
        print(f"  Expected Return: {result['expected_return_percent']:.1f}%")
        print(f"  Growth Horizon: {result['growth_horizon_months']} months")
        print(f"  Harvest Window: {result['harvest_window_start']}")
        
    except Exception as e:
        print(f"\n❌ PREDICTION FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    print()

print("=" * 80)
print("Testing Complete!")
print("=" * 80)
