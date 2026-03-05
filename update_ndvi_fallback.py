"""
NDVI Fallback Data Generator
Gujarat Crop Price Forecasting System

This script generates fallback NDVI values for months where data is not available
in the CSV file (e.g., for 2025-2026).

Strategy:
1. Uses the same month from previous year as a fallback
2. Applies a small seasonal adjustment factor
3. Ensures values stay within valid NDVI range (0.0 - 1.0)

Usage:
    python update_ndvi_fallback.py
    python update_ndvi_fallback.py --year 2026 --month 3
"""

import os
import sys
import pandas as pd
import argparse
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from src.config import DISTRICT_COORDS


def get_latest_ndvi_csv() -> str:
    """Find the latest NDVI CSV file."""
    ndvi_dir = "NDVI"
    csv_files = [
        f for f in os.listdir(ndvi_dir)
        if f.endswith('.csv') and 'ndvi' in f.lower()
    ]
    
    if not csv_files:
        raise FileNotFoundError("No NDVI CSV files found in NDVI/ directory")
    
    # Get the most recent file
    csv_files.sort(reverse=True)
    return os.path.join(ndvi_dir, csv_files[0])


def generate_fallback_ndvi(
    csv_path: str,
    target_year: int,
    target_month: int,
    districts: list = None
) -> pd.DataFrame:
    """
    Generate fallback NDVI values for target year-month.
    
    Uses same month from previous year with seasonal adjustment.
    
    Args:
        csv_path: Path to NDVI CSV file
        target_year: Target year (e.g., 2026)
        target_month: Target month (1-12)
        districts: List of districts (default: all from DISTRICT_COORDS)
    
    Returns:
        DataFrame with fallback NDVI values
    """
    
    if districts is None:
        districts = list(DISTRICT_COORDS.keys())
    
    # Load existing NDVI data
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    
    # Get latest available year
    latest_year = df['year'].max()
    
    print(f"📊 Generating NDVI fallback for {target_year}-{target_month:02d}")
    print(f"   Latest available data: {latest_year}")
    
    # Find data from the same month in previous year(s)
    fallback_data = []
    
    for district in districts:
        # Try to find data for this district and month
        district_data = df[
            (df['district'].str.lower() == district.lower()) &
            (df['month'] == target_month)
        ].sort_values('year', ascending=False)
        
        if district_data.empty:
            print(f"   ⚠️  No historical data for {district} in month {target_month}")
            # Use average NDVI across all months for this district
            fallback_value = df[
                df['district'].str.lower() == district.lower()
            ]['monthly_ndvi_mean'].mean()
            
            if pd.isna(fallback_value):
                fallback_value = 0.5  # Default NDVI
                
        else:
            # Use the most recent year's value for this month
            fallback_value = district_data.iloc[0]['monthly_ndvi_mean']
            
            # Apply a small random variation (±5%) to simulate natural variation
            import random
            variation = random.uniform(-0.05, 0.05)
            fallback_value = fallback_value * (1 + variation)
        
        # Ensure valid NDVI range
        fallback_value = max(0.0, min(1.0, fallback_value))
        
        fallback_data.append({
            'district': district,
            'date': f"{target_year}-{target_month:02d}-01",
            'year': target_year,
            'month': target_month,
            'monthly_ndvi_mean': fallback_value,
            'source': f'fallback_from_{latest_year}',
            'is_fallback': True
        })
        
        print(f"   ✓ {district}: {fallback_value:.4f}")
    
    return pd.DataFrame(fallback_data)


def append_to_csv(
    csv_path: str,
    fallback_df: pd.DataFrame,
    backup: bool = True
) -> None:
    """
    Append fallback data to the NDVI CSV file.
    
    Args:
        csv_path: Path to NDVI CSV
        fallback_df: DataFrame with fallback values
        backup: Create a backup before modifying
    """
    
    if backup:
        backup_path = csv_path.replace('.csv', '_backup.csv')
        import shutil
        shutil.copy2(csv_path, backup_path)
        print(f"📦 Backup created: {backup_path}")
    
    # Load existing data
    existing_df = pd.read_csv(csv_path)
    existing_df['date'] = pd.to_datetime(existing_df['date'])
    
    # Check if data already exists for target period
    fallback_df['date'] = pd.to_datetime(fallback_df['date'])
    
    # Remove any existing entries for the same year-month-district
    for _, row in fallback_df.iterrows():
        existing_df = existing_df[
            ~((existing_df['date'] == row['date']) &
              (existing_df['district'].str.lower() == row['district'].lower()))
        ]
    
    # Append new fallback data
    combined_df = pd.concat([existing_df, fallback_df], ignore_index=True)
    combined_df = combined_df.sort_values(['date', 'district'])
    
    # Ensure proper columns
    required_cols = ['district', 'date', 'monthly_ndvi_mean']
    optional_cols = ['year', 'month', 'source', 'is_fallback']
    
    output_cols = required_cols + [
        col for col in optional_cols if col in combined_df.columns
    ]
    
    # Save
    combined_df[output_cols].to_csv(csv_path, index=False)
    print(f"✅ Updated {csv_path}")
    print(f"   Total records: {len(combined_df)}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate fallback NDVI data for missing months'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=datetime.now().year,
        help='Target year (default: current year)'
    )
    parser.add_argument(
        '--month',
        type=int,
        default=datetime.now().month,
        help='Target month 1-12 (default: current month)'
    )
    parser.add_argument(
        '--csv',
        type=str,
        help='Path to NDVI CSV file (default: auto-detect latest)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backup before modifying CSV'
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview fallback data without saving'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if args.month < 1 or args.month > 12:
        print("❌ Error: Month must be between 1 and 12")
        sys.exit(1)
    
    # Get NDVI CSV path
    csv_path = args.csv
    if not csv_path:
        try:
            csv_path = get_latest_ndvi_csv()
        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    print(f"📁 Using NDVI CSV: {csv_path}")
    
    # Generate fallback data
    try:
        fallback_df = generate_fallback_ndvi(
            csv_path=csv_path,
            target_year=args.year,
            target_month=args.month
        )
        
        print(f"\n📊 Generated {len(fallback_df)} fallback NDVI records")
        
        if args.preview:
            print("\n📋 Preview of fallback data:")
            print(fallback_df.to_string())
            print("\nℹ️  Run without --preview to save to CSV")
        else:
            # Append to CSV
            append_to_csv(
                csv_path=csv_path,
                fallback_df=fallback_df,
                backup=not args.no_backup
            )
            print("\n✅ Fallback NDVI data added successfully!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
