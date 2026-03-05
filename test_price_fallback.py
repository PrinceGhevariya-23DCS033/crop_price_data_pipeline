"""Test the smart price fallback system"""

import sys
sys.path.insert(0, 'src')

from data_fetchers import MandiPriceFetcher
from datetime import datetime

print("=" * 80)
print("TESTING SMART PRICE FALLBACK SYSTEM")
print("=" * 80)

mandi = MandiPriceFetcher()

# Test cases
test_cases = [
    ("Garlic", "Ahmadabad", datetime(2024, 2, 15)),
    ("Onion", "Rajkot", datetime(2024, 1, 15)),
    ("Wheat", "Vadodara", datetime(2023, 12, 15)),
]

for commodity, district, ref_date in test_cases:
    print(f"\n{'='*80}")
    print(f"Testing: {commodity} in {district}")
    print(f"Reference Date: {ref_date.strftime('%Y-%m-%d')}")
    print(f"{'='*80}")
    
    result = mandi.get_current_price_with_fallback(
        commodity=commodity,
        district=district,
        reference_date=ref_date
    )
    
    if result:
        print(f"\n✓ Price Data Found!")
        print(f"  Price: ₹{result['monthly_mean_price']:.2f}")
        print(f"  Source: {result['price_source']}")
        print(f"  Data Until: {result['data_until_date']}")
        print(f"  Is Recent: {result['is_recent']}")
        print(f"  Days Window: {result['days_window']}")
        
        if 'warning' in result:
            print(f"  ⚠️  WARNING: {result['warning']}")
    else:
        print(f"\n❌ No price data found for {commodity} in {district}")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
