"""
Test Agrimart API to find correct district and commodity names
"""

import sys
import os
sys.path.insert(0, 'src')

from data_fetchers import MandiPriceFetcher

print("=" * 80)
print("AGRIMART API - FINDING CORRECT NAMES")
print("=" * 80)

try:
    mandi = MandiPriceFetcher()
    print("✓ MandiPriceFetcher initialized\n")
    
    # Test 1: Fetch data for Gujarat without filters
    print("TEST 1: Fetching recent Gujarat data (no filters)...")
    print("-" * 80)
    
    df = mandi.fetch_latest_prices(
        state="Gujarat",
        limit=500
    )
    
    if df.empty:
        print("❌ No data returned even without filters!")
    else:
        print(f"✓ Fetched {len(df)} records\n")
        
        print("Unique Districts in API:")
        districts = df['District'].unique()
        for i, dist in enumerate(sorted(districts), 1):
            print(f"  {i:2d}. {dist}")
        
        print(f"\n\nUnique Commodities in API (first 30):")
        commodities = df['Commodity'].unique()
        for i, comm in enumerate(sorted(commodities)[:30], 1):
            print(f"  {i:2d}. {comm}")
        
        print(f"\n\nDate Range:")
        print(f"  Latest: {df['Arrival_Date'].max()}")
        print(f"  Oldest: {df['Arrival_Date'].min()}")
        
        # Test 2: Try different variations of Ahmedabad
        print("\n\n" + "=" * 80)
        print("TEST 2: Testing different spellings of Ahmedabad")
        print("=" * 80)
        
        ahmedabad_variations = [
            "Ahmedabad", "Ahmadabad", "Ahmed" "Ahmednagar",
            "AHMEDABAD", "ahmedabad"
        ]
        
        for variation in ahmedabad_variations:
            df_test = mandi.fetch_latest_prices(
                state="Gujarat",
                district=variation,
                limit=100
            )
            
            status = "✓ FOUND" if not df_test.empty else "❌ NOT FOUND"
            count = len(df_test) if not df_test.empty else 0
            print(f"  '{variation}': {status} ({count} records)")
        
        # Test 3: Try different commodity names
        print("\n\n" + "=" * 80)
        print("TEST 3: Testing commodity names")
        print("=" * 80)
        
        commodity_variations = [
            "Garlic", "GARLIC", "garlic",
            "Ajwan", "AJWAN", "ajwan",
            "Onion", "ONION", "onion",
            "Wheat", "WHEAT", "wheat"
        ]
        
        for comm in commodity_variations:
            df_test = mandi.fetch_latest_prices(
                state="Gujarat",
                commodity=comm,
                limit=100
            )
            
            status = "✓ FOUND" if not df_test.empty else "❌ NOT FOUND"
            count = len(df_test) if not df_test.empty else 0
            print(f"  '{comm}': {status} ({count} records)")
        
        # Test 4: Check if data exists for actual district names from API
        print("\n\n" + "=" * 80)
        print("TEST 4: Sample data from actual API district names")
        print("=" * 80)
        
        if len(districts) > 0:
            test_district = districts[0]
            print(f"\nTesting with actual district: '{test_district}'")
            
            df_actual = mandi.fetch_latest_prices(
                state="Gujarat",
                district=test_district,
                limit=200
            )
            
            if not df_actual.empty:
                print(f"✓ Found {len(df_actual)} records")
                print(f"\nCommodities in {test_district}:")
                for comm in sorted(df_actual['Commodity'].unique())[:20]:
                    print(f"  - {comm}")
                
                print(f"\nSample records:")
                print(df_actual[['Commodity', 'District', 'Arrival_Date', 'Modal_Price']].head(5).to_string())

except Exception as e:
    print(f"❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
