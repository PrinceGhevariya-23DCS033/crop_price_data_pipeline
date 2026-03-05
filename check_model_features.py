"""Check what features the model expects"""

import sys
sys.path.insert(0, 'src')

import joblib

print("=" * 80)
print("MODEL FEATURE COLUMNS")
print("=" * 80)

# Load feature columns
feature_columns = joblib.load("production_model/feature_columns.pkl")

print(f"\nTotal features: {len(feature_columns)}")
print("\nFeature list:")
for i, feat in enumerate(feature_columns, 1):
    print(f"  {i:2d}. {feat}")

print("\n" + "=" * 80)
print("CHECKING FOR PROBLEMATIC FEATURES")
print("=" * 80)

problematic = ['momentum_1', 'momentum_3', 'rain_anomaly', 'ndvi_momentum_3']
training_equivalent = ['price_mom_1', 'price_mom_3', 'rain_dev', 'ndvi_trend_3']

print("\nModel expects vs Training creates:")
for model_feat, train_feat in zip(problematic, training_equivalent):
    in_model = "✓" if model_feat in feature_columns else "❌"
    print(f"  {in_model} {model_feat:20s} (training creates: {train_feat})")

print("\n" + "=" * 80)
