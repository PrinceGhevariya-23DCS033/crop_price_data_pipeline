"""
Quick Test Script
Gujarat Crop Price Forecasting System

Tests the inference pipeline without starting the full API.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
import numpy as np
from inference import CropPricePredictor


def test_model_loading():
    """Test if model loads correctly."""
    print("=" * 60)
    print("Test 1: Model Loading")
    print("=" * 60)
    
    try:
        predictor = CropPricePredictor(model_dir="../production_model")
        print("✓ Model loaded successfully")
        print(f"  Model type: {predictor.metadata['model_type']}")
        print(f"  Test R²: {predictor.metadata['r2_test']}")
        print(f"  Test MAPE: {predictor.metadata['mape_test']}%")
        return predictor
    except Exception as e:
        print(f"✗ Model loading failed: {e}")
        return None


def test_supported_crops(predictor):
    """Test crop listing."""
    print("\n" + "=" * 60)
    print("Test 2: Supported Crops")
    print("=" * 60)
    
    try:
        crops = predictor.get_supported_crops()
        print(f"✓ Total crops supported: {len(crops)}")
        print(f"  Sample crops: {', '.join(crops[:10])}")
        return True
    except Exception as e:
        print(f"✗ Crop listing failed: {e}")
        return False


def test_crop_horizons(predictor):
    """Test crop horizon retrieval."""
    print("\n" + "=" * 60)
    print("Test 3: Crop Growth Horizons")
    print("=" * 60)
    
    test_crops = ["Garlic", "Wheat", "Cotton", "Tomato", "Onion"]
    
    for crop in test_crops:
        try:
            horizon = predictor.get_crop_horizon(crop)
            print(f"  {crop}: {horizon} months")
        except Exception as e:
            print(f"  {crop}: Error - {e}")


def test_feature_engineering(predictor):
    """Test feature engineering pipeline."""
    print("\n" + "=" * 60)
    print("Test 4: Feature Engineering")
    print("=" * 60)
    
    try:
        # Create sample data (24 months)
        dates = pd.date_range(start='2023-01-01', periods=24, freq='MS')
        
        df = pd.DataFrame({
            'commodity': ['Garlic'] * 24,
            'district': ['Ahmedabad'] * 24,
            'date': dates,
            'year': dates.year,
            'month': dates.month,
            'monthly_mean_price': np.random.uniform(4000, 6000, 24),
            'days_traded': [20] * 24,
            'monthly_rain_sum': np.random.uniform(0, 100, 24),
            'monthly_rain_mean': np.random.uniform(0, 5, 24),
            'monthly_ndvi_mean': np.random.uniform(0.4, 0.7, 24)
        })
        
        # Apply feature engineering
        df_engineered = predictor.engineer_features(df)
        
        print(f"✓ Feature engineering successful")
        print(f"  Input columns: {len(df.columns)}")
        print(f"  Output columns: {len(df_engineered.columns)}")
        print(f"  New features created: {len(df_engineered.columns) - len(df.columns)}")
        
        return df_engineered
    
    except Exception as e:
        print(f"✗ Feature engineering failed: {e}")
        return None


def test_prediction(predictor, df_engineered):
    """Test prediction with sample data."""
    print("\n" + "=" * 60)
    print("Test 5: Price Prediction")
    print("=" * 60)
    
    if df_engineered is None:
        print("✗ Skipping - no engineered features available")
        return False
    
    try:
        # Use last month's data for prediction
        current_price = df_engineered.iloc[-1]['monthly_mean_price']
        
        result = predictor.predict(
            commodity="Garlic",
            district="Ahmedabad",
            current_price=current_price,
            historical_data=df_engineered.iloc[:-1],  # All but last row
            month=12,
            year=2024,
            monthly_rain_sum=50,
            monthly_rain_mean=2.5,
            monthly_ndvi_mean=0.6,
            days_traded=20
        )
        
        print("✓ Prediction successful")
        print(f"\n  Prediction Results:")
        print(f"  ------------------")
        print(f"  Commodity: {result['commodity']}")
        print(f"  District: {result['district']}")
        print(f"  Current Price: ₹{result['current_price']:.2f}")
        print(f"  Predicted Harvest Price: ₹{result['predicted_harvest_price']:.2f}")
        print(f"  Expected Return: {result['expected_return_percent']:.2f}%")
        print(f"  Growth Horizon: {result['growth_horizon_months']} months")
        print(f"  Harvest Window: {result['harvest_window_start']}")
        
        return True
    
    except Exception as e:
        print(f"✗ Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests."""
    print("\n🧪 Gujarat Crop Price Forecasting - Test Suite\n")
    
    results = []
    
    # Test 1: Model loading
    predictor = test_model_loading()
    results.append(predictor is not None)
    
    if predictor is None:
        print("\n❌ Critical failure: Cannot proceed without model")
        return
    
    # Test 2: Supported crops
    results.append(test_supported_crops(predictor))
    
    # Test 3: Crop horizons
    test_crop_horizons(predictor)
    
    # Test 4: Feature engineering
    df_engineered = test_feature_engineering(predictor)
    results.append(df_engineered is not None)
    
    # Test 5: Prediction
    results.append(test_prediction(predictor, df_engineered))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! System is ready.")
    else:
        print("⚠ Some tests failed. Check errors above.")


if __name__ == "__main__":
    run_all_tests()
