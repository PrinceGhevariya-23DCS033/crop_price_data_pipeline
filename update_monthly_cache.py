"""
Monthly Cache Update Script
Gujarat Crop Price Forecasting System

Run this script monthly (after 16-20th) to refresh cached data:
- Latest mandi prices (last 30 days average)
- Rainfall data (previous month)
- NDVI data (previous month, available after 16-20th)

Usage:
    python update_monthly_cache.py
    
    # Or for specific month:
    python update_monthly_cache.py --year 2024 --month 1

Schedule:
    Run between 20th-25th of each month to get latest NDVI
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.monthly_cache import MonthlyDataCache
from src.data_fetchers import MandiPriceFetcher, WeatherFetcher, NDVIFetcher
from src.config import DISTRICT_COORDS, normalize_district_name


def get_all_commodities_from_processed() -> list:
    """Get list of all commodities from processed directory."""
    processed_dir = "processed"
    
    if not os.path.exists(processed_dir):
        print(f"⚠ Processed directory not found: {processed_dir}")
        return []
    
    commodities = []
    for file in os.listdir(processed_dir):
        if file.endswith("_final.csv"):
            commodity = file.replace("_final.csv", "").replace("_", " ").title()
            commodities.append(commodity)
    
    return sorted(commodities)


def get_all_districts() -> list:
    """Get list of all districts from config."""
    return sorted(list(DISTRICT_COORDS.keys()))


def update_price_cache(
    cache: MonthlyDataCache,
    fetcher: MandiPriceFetcher,
    commodities: list,
    districts: list,
    year: int,
    month: int
):
    """
    Update price cache for all commodity-district combinations.
    
    Uses 30-day average from API or CSV fallback.
    """
    print("\n" + "="*70)
    print("📊 UPDATING PRICE CACHE")
    print("="*70)
    
    total = len(commodities) * len(districts)
    current = 0
    success = 0
    failed = 0
    
    for commodity in commodities:
        for district in districts:
            current += 1
            print(f"\n[{current}/{total}] {commodity} - {district}")
            
            try:
                # Use get_current_price_with_fallback (30-day average)
                price_data = fetcher.get_current_price_with_fallback(
                    commodity=commodity,
                    district=district,
                    reference_date=datetime(year, month, 20),  # Use 20th as reference
                    days_15=15,
                    days_30=30
                )
                
                if price_data:
                    cache.save_price(
                        commodity=commodity,
                        district=district,
                        year=year,
                        month=month,
                        price_data=price_data
                    )
                    print(f"  ✓ Price: ₹{price_data['monthly_mean_price']:.2f} ({price_data['price_source']})")
                    success += 1
                else:
                    print(f"  ✗ No price data available")
                    failed += 1
            
            except Exception as e:
                print(f"  ✗ Error: {e}")
                failed += 1
    
    print(f"\n{'='*70}")
    print(f"Price Cache Update: {success} success, {failed} failed")
    print(f"{'='*70}")


def update_rainfall_cache(
    cache: MonthlyDataCache,
    fetcher: WeatherFetcher,
    districts: list,
    year: int,
    month: int
):
    """
    Update rainfall cache for all districts.
    
    Fetches previous month's rainfall (current month data may be incomplete).
    """
    print("\n" + "="*70)
    print("🌧️  UPDATING RAINFALL CACHE")
    print("="*70)
    
    # Use previous month's data (more reliable)
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    
    print(f"Fetching data for: {prev_year}-{prev_month:02d}")
    
    success = 0
    failed = 0
    
    for i, district in enumerate(districts, 1):
        print(f"\n[{i}/{len(districts)}] {district}")
        
        try:
            rainfall_data = fetcher.get_monthly_rainfall(
                district=district,
                year=prev_year,
                month=prev_month
            )
            
            if rainfall_data:
                cache.save_rainfall(
                    district=district,
                    year=prev_year,
                    month=prev_month,
                    rainfall_data=rainfall_data
                )
                print(f"  ✓ Rainfall: {rainfall_data['monthly_rain_sum']:.1f}mm " +
                      f"(avg: {rainfall_data['monthly_rain_mean']:.1f}mm/day)")
                success += 1
            else:
                print(f"  ✗ No rainfall data available")
                failed += 1
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"Rainfall Cache Update: {success} success, {failed} failed")
    print(f"{'='*70}")


def update_ndvi_cache(
    cache: MonthlyDataCache,
    fetcher: NDVIFetcher,
    districts: list,
    commodities: list,
    year: int,
    month: int
):
    """
    Update NDVI cache for all districts.
    
    NDVI data is available after 16-20th of month for previous month.
    Uses CSV fallback since it has pre-computed NDVI.
    """
    print("\n" + "="*70)
    print("🛰️  UPDATING NDVI CACHE")
    print("="*70)
    
    # Use previous month's data
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    
    print(f"Fetching data for: {prev_year}-{prev_month:02d}")
    
    success = 0
    failed = 0
    
    for i, district in enumerate(districts, 1):
        print(f"\n[{i}/{len(districts)}] {district}")
        
        try:
            # Use first commodity for CSV lookup (NDVI is by district, not commodity-specific)
            sample_commodity = commodities[0] if commodities else "Wheat"
            
            ndvi_data = fetcher.get_ndvi_from_csv(
                commodity=sample_commodity,
                district=district,
                year=prev_year,
                month=prev_month
            )
            
            if ndvi_data:
                cache.save_ndvi(
                    district=district,
                    year=prev_year,
                    month=prev_month,
                    ndvi_data=ndvi_data
                )
                print(f"  ✓ NDVI: {ndvi_data['monthly_ndvi_mean']:.4f} " +
                      f"(source: {ndvi_data.get('source', 'CSV')})")
                success += 1
            else:
                print(f"  ✗ No NDVI data available")
                failed += 1
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"NDVI Cache Update: {success} success, {failed} failed")
    print(f"{'='*70}")


def main():
    """Main update function."""
    
    parser = argparse.ArgumentParser(
        description="Update monthly data cache for crop price prediction"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Year to update (default: current year)"
    )
    parser.add_argument(
        "--month",
        type=int,
        default=None,
        help="Month to update (default: current month)"
    )
    parser.add_argument(
        "--prices-only",
        action="store_true",
        help="Update only prices"
    )
    parser.add_argument(
        "--rainfall-only",
        action="store_true",
        help="Update only rainfall"
    )
    parser.add_argument(
        "--ndvi-only",
        action="store_true",
        help="Update only NDVI"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompts (for CI/automated runs)"
    )
    
    args = parser.parse_args()
    
    # Get current date
    now = datetime.now()
    year = args.year or now.year
    month = args.month or now.month
    
    print("="*70)
    print(" GUJARAT CROP PRICE FORECASTING - MONTHLY CACHE UPDATE")
    print("="*70)
    print(f"Update Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Period: {year}-{month:02d}")
    
    # Warning if running before 20th
    if now.day < 20 and not (args.year or args.month):
        print("\n⚠️  WARNING: NDVI data for previous month is typically available after 16-20th")
        print("   Consider running this script between 20-25th of each month.")
        if not args.yes:
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                print("Aborted.")
                return
        else:
            print("   --yes flag set, continuing automatically.")
    
    # Initialize cache and fetchers
    print("\n" + "="*70)
    print("INITIALIZING")
    print("="*70)
    
    cache = MonthlyDataCache()
    
    try:
        price_fetcher = MandiPriceFetcher()
        print("✓ Price fetcher initialized")
    except Exception as e:
        print(f"✗ Price fetcher failed: {e}")
        price_fetcher = None
    
    weather_fetcher = WeatherFetcher()
    print("✓ Weather fetcher initialized")
    
    ndvi_fetcher = NDVIFetcher()
    print("✓ NDVI fetcher initialized")
    
    # Get commodities and districts
    commodities = get_all_commodities_from_processed()
    districts = get_all_districts()
    
    print(f"\n Found {len(commodities)} commodities")
    print(f"Found {len(districts)} districts")
    
    # Update cache components
    update_all = not (args.prices_only or args.rainfall_only or args.ndvi_only)
    
    if update_all or args.prices_only:
        if price_fetcher:
            update_price_cache(cache, price_fetcher, commodities, districts, year, month)
        else:
            print("\n⚠️  Skipping price update (fetcher not available)")
    
    if update_all or args.rainfall_only:
        update_rainfall_cache(cache, weather_fetcher, districts, year, month)
    
    if update_all or args.ndvi_only:
        update_ndvi_cache(cache, ndvi_fetcher, districts, commodities, year, month)
    
    # Update metadata
    cache.update_metadata(year, month, commodities, districts)
    
    # Print final stats
    print("\n" + "="*70)
    print("✅ CACHE UPDATE COMPLETE")
    print("="*70)
    
    stats = cache.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  Last Updated: {stats['last_updated']}")
    print(f"  Period: {stats['update_year']}-{stats['update_month']:02d}")
    print(f"  Price Entries: {stats['total_price_entries']}")
    print(f"  Rainfall Entries: {stats['total_rainfall_entries']}")
    print(f"  NDVI Entries: {stats['total_ndvi_entries']}")
    print(f"  Commodities: {stats['commodities_count']}")
    print(f"  Districts: {stats['districts_count']}")
    print(f"  Status: {'✓ Current' if stats['is_current'] else '⚠ Outdated'}")
    
    print("\n" + "="*70)
    print("Next update recommended: 20-25th of next month")
    print("="*70)


if __name__ == "__main__":
    main()
