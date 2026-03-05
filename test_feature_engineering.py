"""
Test Feature Engineering
Verify that inference feature engineering produces correct features
"""

import sys
import os
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
from inference import CropPricePredictor

print("=" * 80)
print("TESTING FEATURE ENGINEERING")
print("=" * 80)

# Load a sample CSV to test
csv_file = "processed/onion_final.csv"

if os.path.exists(csv_file):
    print(f"\n✓ Loading {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    
    # Check if training features exist in CSV
    training_features = [
        'price_lag_1', 'price_lag_2', 'price_lag_3', 'price_lag_6', 'price_lag_12',
        'price_roll_mean_3', 'price_roll_mean_6', 'price_roll_std_3', 'price_roll_std_6',
        'price_mom_1', 'price_mom_3',
        'rain_roll_3', 'rain_dev',
        'ndvi_lag_1', 'ndvi_trend_3',
        'month_sin', 'month_cos'
    ]
    
    print("\n" + "=" * 80)
    print("CHECKING TRAINING FEATURES IN CSV")
    print("=" * 80)
    
    missing_in_csv = []
    for feat in training_features:
        if feat in df.columns:
            print(f"  ✓ {feat}")
        else:
            print(f"  ❌ {feat} - MISSING!")
            missing_in_csv.append(feat)
    
    if missing_in_csv:
        print(f"\n⚠️  Missing {len(missing_in_csv)} features in CSV!")
        print("  You may need to re-run feature engineering on your CSV files.")
    
    # Now test inference feature engineering
    print("\n" + "=" * 80)
    print("TESTING INFERENCE FEATURE ENGINEERING")
    print("=" * 80)
    
    try:
        predictor = CropPricePredictor(model_dir="production_model")
        print("✓ Predictor loaded")
        
        # Get sample data for one commodity-district
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # Take last 20 months of data for one district
        sample_district = df['district'].iloc[0] if 'district' in df.columns else 'unknown'
        sample_commodity = df['commodity'].iloc[0] if 'commodity' in df.columns else 'Onion'
        
        sample_df = df.head(20).copy()
        
        print(f"\n  Testing with: {sample_commodity} in {sample_district}")
        print(f"  Input shape: {sample_df.shape}")
        
        # Apply feature engineering
        engineered_df = predictor.engineer_features(sample_df)
        
        print(f"  Output shape: {engineered_df.shape}")
        
        # Check which features were created
        print("\n  Features created by inference:")
        inference_features = [col for col in engineered_df.columns if col in training_features]
        
        for feat in training_features:
            if feat in engineered_df.columns:
                # Check for NaN values
                nan_count = engineered_df[feat].isna().sum()
                sample_val = engineered_df[feat].dropna().iloc[0] if len(engineered_df[feat].dropna()) > 0 else None
                print(f"    ✓ {feat:20s} - NaN: {nan_count:2d}, Sample: {sample_val}")
            else:
                print(f"    ❌ {feat:20s} - NOT CREATED!")
        
        # Show final row (latest month with all features)
        print("\n  Latest row with features:")
        latest = engineered_df.iloc[-1]
        print(f"    Date: {latest.get('date', 'N/A')}")
        print(f"    Price: {latest.get('monthly_mean_price', 'N/A')}")
        print(f"    price_lag_1: {latest.get('price_lag_1', 'N/A')}")
        print(f"    price_mom_1: {latest.get('price_mom_1', 'N/A')}")
        print(f"    rain_roll_3: {latest.get('rain_roll_3', 'N/A')}")
        
        print("\n✓ Feature engineering test complete!")
        
    except Exception as e:
        print(f"\n❌ Feature engineering failed: {e}")
        import traceback
        traceback.print_exc()
        
else:
    print(f"❌ CSV file not found: {csv_file}")

print("\n" + "=" * 80)
