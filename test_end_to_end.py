"""
End-to-End Prediction Test
Test the complete prediction pipeline with real data
"""

import sys
import os
sys.path.insert(0, 'src')

import pandas as pd
from datetime import datetime
from inference import CropPricePredictor
from data_fetchers import MandiPriceFetcher, WeatherFetcher, NDVIFetcher
from config import normalize_district_name

print("=" * 80)
print("END-TO-END PREDICTION TEST")
print("=" * 80)

# Test configuration
TEST_COMMODITY = "Onion"
TEST_DISTRICT = "Rajkot"  # Original name
TEST_YEAR = 2024
TEST_MONTH = 1

print(f"\nTest Configuration:")
print(f"  Commodity: {TEST_COMMODITY}")
print(f"  District: {TEST_DISTRICT} (will normalize to: {normalize_district_name(TEST_DISTRICT)})")
print(f"  Target Month: {TEST_YEAR}-{TEST_MONTH:02d}")

try:
    # Step 1: Load predictor
    print("\n" + "=" * 80)
    print("STEP 1: Load Predictor")
    print("=" * 80)
    predictor = CropPricePredictor(model_dir="production_model")
    print("✓ Predictor loaded successfully")
    
    # Step 2: Fetch historical data
    print("\n" + "=" * 80)
    print("STEP 2: Fetch Historical Data")
    print("=" * 80)
    
    mandi = MandiPriceFetcher()
    historical_data = mandi.fetch_historical_monthly_prices(
        commodity=TEST_COMMODITY,
        district=TEST_DISTRICT,
        months_back=18
    )
    
    if historical_data.empty:
        print(f"❌ No historical data found for {TEST_COMMODITY} in {TEST_DISTRICT}")
        sys.exit(1)
    
    print(f"✓ Loaded {len(historical_data)} months of historical data")
    print(f"  Columns: {list(historical_data.columns)}")
    print(f"  District values in data: {historical_data['district'].unique()}")
    print(f"  Commodity values in data: {historical_data['commodity'].unique()}")
    print(f"  Date range: {historical_data['date'].min()} to {historical_data['date'].max()}")
    
    # Step 3: Get current price
    print("\n" + "=" * 80)
    print("STEP 3: Get Current Price")
    print("=" * 80)
    
    current_price_data = mandi.get_current_price_with_fallback(
        commodity=TEST_COMMODITY,
        district=TEST_DISTRICT,
        reference_date=datetime(TEST_YEAR, TEST_MONTH, 15)
    )
    
    if not current_price_data:
        print(f"❌ No current price data found")
        sys.exit(1)
    
    print(f"✓ {current_price_data['price_source']}")
    print(f"  Price: ₹{current_price_data['monthly_mean_price']:.2f}")
    print(f"  Data until: {current_price_data['data_until_date']}")
    
    # Step 4: Get weather and NDVI
    print("\n" + "=" * 80)
    print("STEP 4: Get Weather and NDVI")
    print("=" * 80)
    
    weather = WeatherFetcher()
    weather_data = weather.get_monthly_rainfall(
        district=TEST_DISTRICT,
        year=TEST_YEAR,
        month=TEST_MONTH
    )
    
    if weather_data:
        print(f"✓ Rainfall: {weather_data['monthly_rain_sum']:.2f}mm")
    else:
        print("⚠ Using default weather data")
        weather_data = {"monthly_rain_sum": 0, "monthly_rain_mean": 0}
    
    ndvi = NDVIFetcher()
    ndvi_data = ndvi.get_monthly_ndvi(
        district=TEST_DISTRICT,
        year=TEST_YEAR,
        month=TEST_MONTH,
        commodity=TEST_COMMODITY  # Pass commodity for CSV fallback
    )
    
    if not ndvi_data:
        print("  ⚠ NDVI data unavailable, using default")
        ndvi_data = {"monthly_ndvi_mean": 0.5}
    else:
        ndvi_source = ndvi_data.get("source", "GEE")
        ndvi_date = ndvi_data.get("data_date", "")
        print(f"  ✓ NDVI: {ndvi_data['monthly_ndvi_mean']:.3f} (from {ndvi_source}" + (f", data date: {ndvi_date}" if ndvi_date else "") + ")")
    
    # Step 5: Make prediction
    print("\n" + "=" * 80)
    print("STEP 5: Make Prediction")
    print("=" * 80)
    
    normalized_district = normalize_district_name(TEST_DISTRICT)
    
    print(f"  Input:")
    print(f"    Commodity: {TEST_COMMODITY}")
    print(f"    District: {normalized_district}")
    print(f"    Current Price: ₹{current_price_data['monthly_mean_price']:.2f}")
    print(f"    Historical months: {len(historical_data)}")
    
    result = predictor.predict(
        commodity=TEST_COMMODITY,
        district=normalized_district,  # Use normalized!
        current_price=current_price_data["monthly_mean_price"],
        historical_data=historical_data,
        month=TEST_MONTH,
        year=TEST_YEAR,
        monthly_rain_sum=weather_data.get("monthly_rain_sum", 0),
        monthly_rain_mean=weather_data.get("monthly_rain_mean", 0),
        monthly_ndvi_mean=ndvi_data.get("monthly_ndvi_mean", 0.5),
        days_traded=current_price_data.get("days_traded", 20)
    )
    
    # Step 6: Display results
    print("\n" + "=" * 80)
    print("STEP 6: Prediction Results")
    print("=" * 80)
    
    print(f"\n✓ PREDICTION SUCCESSFUL!")
    print(f"\n  Commodity: {result['commodity']}")
    print(f"  District: {result['district']}")
    print(f"  Current Price: ₹{result['current_price']:.2f}")
    print(f"  Predicted Harvest Price: ₹{result['predicted_harvest_price']:.2f}")
    print(f"  Expected Return: {result['expected_return_percent']:.2f}%")
    print(f"  Absolute Change: ₹{result['absolute_change']:.2f}")
    print(f"  Growth Horizon: {result['growth_horizon_months']} months")
    print(f"  Harvest Window: {result['harvest_window_start']}")
    
    if result['expected_return_percent'] > 0:
        print(f"\n  📈 RECOMMENDATION: Good opportunity! Price expected to rise.")
    else:
        print(f"\n  📉 CAUTION: Price expected to decline.")
    
    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED!")
    print("=" * 80)
    
except ValueError as e:
    print(f"\n❌ PREDICTION FAILED: {e}")
    import traceback
    traceback.print_exc()
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
