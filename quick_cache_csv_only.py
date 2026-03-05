"""
Quick Monthly Cache Generation - CSV Only (No API calls)
For faster deployment to Hugging Face
"""

import os
import sys
import json
from datetime import datetime
import pandas as pd
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import existing modules
from src.monthly_cache import MonthlyDataCache
from src.config import DISTRICT_COORDS

def quick_cache_from_csv():
    """Generate monthly cache using only CSV data (no API calls)"""
    
    print("="*70)
    print(" QUICK MONTHLY CACHE GENERATION (CSV ONLY)")
    print("="*70)
    print(f"Update Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Period: {datetime.now().strftime('%Y-%m')}\n")
    
    # Initialize cache
    cache = MonthlyDataCache()
    
    # Get all CSV files from processed folder
    processed_dir = Path("processed")
    csv_files = list(processed_dir.glob("*.csv"))
    
    print(f"\nFound {len(csv_files)} commodity CSV files")
    print(f"Found {len(DISTRICT_COORDS)} districts\n")
    
    print("="*70)
    print("GENERATING PRICE CACHE FROM CSV FILES")
    print("="*70)
    
    total_combinations = len(csv_files) * len(DISTRICT_COORDS)
    current = 0
    prices_saved = 0
    
    for csv_file in csv_files:
        # Get commodity name from filename
        commodity_raw = csv_file.stem.replace("_final", "").replace("_", " ").title()
        
        try:
            # Load CSV
            df = pd.read_csv(csv_file)
            
            # Ensure date column is datetime
            df['date'] = pd.to_datetime(df['date'])
            
            for district in DISTRICT_COORDS.keys():
                current += 1
                
                # Filter for this district
                district_data = df[df['district'].str.lower() == district.lower()]
                
                if len(district_data) == 0:
                    continue
                
                # Get most recent price (within last 30 days)
                recent_data = district_data.tail(30)
                
                if len(recent_data) > 0:
                    avg_price = recent_data['monthly_mean_price'].mean()
                    
                    # Save to cache
                    cache.save_price(
                        commodity=commodity_raw,
                        district=district,
                        year=datetime.now().year,
                        month=datetime.now().month,
                        price_data={
                            "monthly_mean_price": float(avg_price),
                            "days_traded": len(recent_data),
                            "data_source": "CSV",
                            "last_date": recent_data['date'].max().strftime('%Y-%m-%d')
                        }
                    )
                    prices_saved += 1
                    
                    if current % 50 == 0:
                        print(f"[{current}/{total_combinations}] Processed {prices_saved} price caches")
        
        except Exception as e:
            print(f"Error processing {csv_file.name}: {e}")
            continue
    
    print(f"\n{'='*70}")
    print(f"Price cache complete: {prices_saved} entries saved")
    print(f"{'='*70}\n")
    
    # Add rainfall data (simple averages for all districts)
    print("="*70)
    print("ADDING DEFAULT RAINFALL DATA")
    print("="*70)
    
    # Use reasonable default values for February in Gujarat
    rainfall_defaults = {
        "ahmadabad": 2.5,
        "rajkot": 1.8,
        "surat": 3.2,
        "vadodara": 2.8,
        "bhavnagar": 2.0,
        "jamnagar": 1.5,
        "junagadh": 2.2,
        "gandhinagar": 2.5,
        "anand": 2.8,
        "patan": 2.0,
        "mehsana": 2.0,
    }
    
    for district in DISTRICT_COORDS.keys():
        rainfall = rainfall_defaults.get(district, 2.5)  # Default 2.5mm for others
        
        cache.save_rainfall(
            district=district,
            year=datetime.now().year,
            month=datetime.now().month,
            rainfall_data={
                "monthly_rain_sum": rainfall,
                "monthly_rain_mean": rainfall / 28,
                "source": "Default",
                "metadata": "Historical average for season"
            }
        )
    
    print(f"Rainfall data added for {len(DISTRICT_COORDS)} districts\n")
    
    # Add NDVI data (reasonable defaults)
    print("="*70)
    print("ADDING DEFAULT NDVI DATA")
    print("="*70)
    
    for district in DISTRICT_COORDS.keys():
        ndvi = 0.45  # Moderate vegetation for winter/spring
        
        cache.save_ndvi(
            district=district,
            year=datetime.now().year,
            month=datetime.now().month,
            ndvi_data={
                "monthly_ndvi_mean": ndvi,
                "source": "Default",
                "metadata": "Historical average for season"
            }
        )
    
    print(f"NDVI data added for {len(DISTRICT_COORDS)} districts\n")
    
    # Final summary
    print("="*70)
    print("CACHE GENERATION COMPLETE")
    print("="*70)
    
    status = cache.get_cache_stats()
    print(f"\nTotal cache entries:")
    print(f"  - Prices: {status['total_price_entries']}")
    print(f"  - Rainfall: {status['total_rainfall_entries']}")
    print(f"  - NDVI: {status['total_ndvi_entries']}")
    print(f"\nCache location: monthly_cache/")
    print(f"Ready for deployment to Hugging Face!")
    print("="*70)

if __name__ == "__main__":
    quick_cache_from_csv()
