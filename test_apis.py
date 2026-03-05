"""
API Testing Script
Test all data sources for Gujarat Crop Price Forecasting System
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, 'src')

from data_fetchers import MandiPriceFetcher, WeatherFetcher, NDVIFetcher
from config import DISTRICT_COORDS

print("=" * 80)
print("GUJARAT CROP PRICE FORECASTING - API TESTING")
print("=" * 80)

# Test configurations
TEST_CROPS = ["Ajwan", "Garlic", "Wheat", "Onion", "Tomato"]
TEST_DISTRICTS = ["Ahmadabad", "Rajkot", "Surat", "Vadodara"]
TEST_YEAR = 2024
TEST_MONTH = 2

print(f"\nTest Configuration:")
print(f"  Crops: {', '.join(TEST_CROPS)}")
print(f"  Districts: {', '.join(TEST_DISTRICTS[:2])} (showing 2 for brevity)")
print(f"  Target Month: {TEST_YEAR}-{TEST_MONTH:02d}")
print()

# ============================================================================
# TEST 1: MANDI PRICE API (data.gov.in)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1: MANDI PRICE API (data.gov.in Agmarknet)")
print("=" * 80)

try:
    mandi = MandiPriceFetcher()
    print("✓ MandiPriceFetcher initialized")
    
    # Test fetch latest prices
    print("\n1.1 Testing fetch_latest_prices()...")
    print("-" * 80)
    
    for district in TEST_DISTRICTS[:1]:  # Just test one district
        print(f"\nDistrict: {district}")
        
        df = mandi.fetch_latest_prices(
            state="Gujarat",
            district=district,
            limit=100
        )
        
        if df.empty:
            print(f"  ❌ No data returned for {district}")
        else:
            print(f"  ✓ Fetched {len(df)} records")
            print(f"  Commodities found: {df['Commodity'].unique()[:5].tolist()}")
            print(f"  Date range: {df['Arrival_Date'].min()} to {df['Arrival_Date'].max()}")
            print(f"  Sample data:")
            print(df[['Commodity', 'District', 'Arrival_Date', 'Modal_Price']].head(3).to_string())
    
    # Test compute monthly average
    print("\n\n1.2 Testing compute_monthly_average()...")
    print("-" * 80)
    
    for crop in TEST_CROPS[:2]:  # Test first 2 crops
        print(f"\n{crop} in Ahmadabad ({TEST_YEAR}-{TEST_MONTH:02d}):")
        
        result = mandi.compute_monthly_average(
            commodity=crop,
            district="Ahmadabad",
            year=TEST_YEAR,
            month=TEST_MONTH
        )
        
        if result:
            print(f"  ✓ Monthly Mean Price: ₹{result['monthly_mean_price']:.2f}")
            print(f"  Days Traded: {result['days_traded']}")
            print(f"  Price Range: ₹{result['min_price']:.2f} - ₹{result['max_price']:.2f}")
        else:
            print(f"  ❌ No data available")
    
    # Test fetch with different date ranges
    print("\n\n1.3 Testing recent data availability...")
    print("-" * 80)
    
    df_recent = mandi.fetch_latest_prices(
        state="Gujarat",
        commodity="Garlic",
        district="Ahmadabad",
        limit=1000
    )
    
    if not df_recent.empty:
        print(f"\n  Garlic in Ahmadabad - Recent Data:")
        print(f"  Total records: {len(df_recent)}")
        print(f"  Latest date: {df_recent['Arrival_Date'].max()}")
        print(f"  Oldest date: {df_recent['Arrival_Date'].min()}")
        
        # Group by month
        df_recent['YearMonth'] = df_recent['Arrival_Date'].dt.to_period('M')
        monthly_counts = df_recent.groupby('YearMonth').size()
        print(f"\n  Records by month (last 6 months):")
        for period, count in monthly_counts.tail(6).items():
            print(f"    {period}: {count} records")

except Exception as e:
    print(f"❌ MANDI API TEST FAILED: {e}")
    import traceback
    traceback.print_exc()


# ============================================================================
# TEST 2: WEATHER API (Open-Meteo)
# ============================================================================
print("\n\n" + "=" * 80)
print("TEST 2: WEATHER API (Open-Meteo)")
print("=" * 80)

try:
    weather = WeatherFetcher()
    print("✓ WeatherFetcher initialized")
    print(f"✓ Loaded {len(weather.district_coords)} district coordinates")
    
    print("\n2.1 Testing get_monthly_rainfall()...")
    print("-" * 80)
    
    for district in TEST_DISTRICTS[:2]:
        print(f"\n{district} ({TEST_YEAR}-{TEST_MONTH:02d}):")
        
        result = weather.get_monthly_rainfall(
            district=district,
            year=TEST_YEAR,
            month=TEST_MONTH
        )
        
        if result:
            print(f"  ✓ Monthly Rain Sum: {result['monthly_rain_sum']:.2f} mm")
            print(f"  ✓ Monthly Rain Mean: {result['monthly_rain_mean']:.2f} mm/day")
        else:
            print(f"  ❌ No weather data")
    
    # Test recent month
    print(f"\n\n2.2 Testing recent month (January 2026)...")
    print("-" * 80)
    
    result_recent = weather.get_monthly_rainfall(
        district="Ahmadabad",
        year=2026,
        month=1
    )
    
    if result_recent:
        print(f"  Ahmadabad January 2026:")
        print(f"  ✓ Rain Sum: {result_recent['monthly_rain_sum']:.2f} mm")
        print(f"  ✓ Rain Mean: {result_recent['monthly_rain_mean']:.2f} mm/day")
    else:
        print(f"  ❌ No data for recent month")

except Exception as e:
    print(f"❌ WEATHER API TEST FAILED: {e}")
    import traceback
    traceback.print_exc()


# ============================================================================
# TEST 3: NDVI API (Google Earth Engine)
# ============================================================================
print("\n\n" + "=" * 80)
print("TEST 3: NDVI API (Google Earth Engine)")
print("=" * 80)

try:
    ndvi = NDVIFetcher()
    print("✓ NDVIFetcher initialized")
    
    if hasattr(ndvi, 'ee') and ndvi.ee:
        print("✓ Google Earth Engine authenticated")
        
        print("\n3.1 Testing get_monthly_ndvi()...")
        print("-" * 80)
        
        for district in TEST_DISTRICTS[:2]:
            print(f"\n{district} ({TEST_YEAR}-{TEST_MONTH:02d}):")
            
            result = ndvi.get_monthly_ndvi(
                district=district,
                year=TEST_YEAR,
                month=TEST_MONTH
            )
            
            if result:
                print(f"  ✓ Monthly NDVI Mean: {result['monthly_ndvi_mean']:.4f}")
            else:
                print(f"  ❌ No NDVI data")
    else:
        print("⚠ Google Earth Engine not available (library not installed)")
        print("  Install: pip install earthengine-api")

except Exception as e:
    print(f"⚠ NDVI API TEST: {e}")


# ============================================================================
# TEST 4: DISTRICT COORDINATES
# ============================================================================
print("\n\n" + "=" * 80)
print("TEST 4: DISTRICT COORDINATES")
print("=" * 80)

print(f"\nTotal districts loaded: {len(DISTRICT_COORDS)}")
print("\nSample coordinates:")
for i, (district, coords) in enumerate(list(DISTRICT_COORDS.items())[:5]):
    print(f"  {district}: {coords}")

print("\nTesting normalization:")
from config import normalize_district_name

test_names = ["Ahmedabad", "Ahmadabad", "ahmadabad", "Vadodara", "Vadodara (Baroda)"]
for name in test_names:
    normalized = normalize_district_name(name)
    in_coords = "✓" if normalized in DISTRICT_COORDS else "❌"
    print(f"  '{name}' → '{normalized}' {in_coords}")


# ============================================================================
# SUMMARY
# ============================================================================
print("\n\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

print("\nAPI Status:")
print("  [1] Mandi Price API (data.gov.in): Check output above")
print("  [2] Weather API (Open-Meteo): Check output above")
print("  [3] NDVI API (Google Earth Engine): Check output above")
print("  [4] District Coordinates: Check output above")

print("\n" + "=" * 80)
print("Testing complete! Review the output above for details.")
print("=" * 80)
