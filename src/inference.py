"""
Production Inference Module
Gujarat Crop Price Forecasting System

Loads trained model and generates harvest-window price predictions.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

try:
    from config import normalize_district_name
except ImportError:
    from src.config import normalize_district_name


class CropPricePredictor:
    """
    Production-ready crop price predictor.
    
    Predicts harvest-window average mandi price for Gujarat crops
    based on current market conditions and environmental factors.
    """
    
    def __init__(self, model_dir: str = "production_model"):
        """
        Load all required production artifacts.
        
        Args:
            model_dir: Directory containing saved model files
        """
        self.model_dir = model_dir
        
        # Load model and encoders
        self.model = joblib.load(os.path.join(model_dir, "crop_price_model.pkl"))
        self.district_encoder = joblib.load(os.path.join(model_dir, "district_encoder.pkl"))
        self.commodity_encoder = joblib.load(os.path.join(model_dir, "commodity_encoder.pkl"))
        
        # Load feature columns (preserve order)
        self.feature_columns = joblib.load(os.path.join(model_dir, "feature_columns.pkl"))
        
        # Load crop-specific growth horizons
        self.crop_horizon = joblib.load(os.path.join(model_dir, "crop_horizon.pkl"))
        
        # Load metadata
        self.metadata = joblib.load(os.path.join(model_dir, "model_metadata.pkl"))
        
        print(f"✓ Model loaded: {self.metadata['model_type']}")
        print(f"✓ Test R²: {self.metadata['r2_test']}")
        print(f"✓ Test MAPE: {self.metadata['mape_test']}%")
    
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply feature engineering pipeline (matches training).
        
        Args:
            df: DataFrame with historical price and environmental data
            
        Returns:
            DataFrame with engineered features
        """
        df = df.copy()
        df = df.sort_values(["commodity", "district", "date"]).reset_index(drop=True)
        
        # ============ LAG FEATURES (PRICE) ============
        for lag in [1, 2, 3, 6, 12]:
            df[f"price_lag_{lag}"] = (
                df.groupby(["commodity", "district"])["monthly_mean_price"]
                .shift(lag)
            )
        
        # ============ ROLLING STATISTICS (PRICE) ============
        for window in [3, 6]:
            df[f"price_roll_mean_{window}"] = (
                df.groupby(["commodity", "district"])["monthly_mean_price"]
                .shift(1)
                .rolling(window)
                .mean()
            )
            
            df[f"price_roll_std_{window}"] = (
                df.groupby(["commodity", "district"])["monthly_mean_price"]
                .shift(1)
                .rolling(window)
                .std()
            )
        
        # ============ MOMENTUM (PRICE) ============
        # Absolute difference (not percentage change)
        df["price_mom_1"] = (
            df.groupby(["commodity", "district"])["monthly_mean_price"].transform(lambda x: x - x.shift(1))
        )
        
        df["price_mom_3"] = (
            df.groupby(["commodity", "district"])["monthly_mean_price"].transform(lambda x: x - x.shift(3))
        )
        
        # ============ VOLATILITY (PRICE) ============
        df["volatility_12"] = (
            df.groupby(["commodity", "district"])["monthly_mean_price"]
            .shift(1)
            .rolling(12)
            .std()
        )
        
        # ============ PRICE RATIOS ============
        epsilon = 1e-10
        df["price_ratio_1"] = df["monthly_mean_price"] / (df["price_lag_1"] + epsilon)
        df["price_ratio_3"] = df["monthly_mean_price"] / (df["price_lag_3"] + epsilon)
        
        # ============ RAIN FEATURES ============
        # Rolling sum for rain (last 3 months total)
        df["rain_roll_3"] = (
            df.groupby(["commodity", "district"])["monthly_rain_sum"]
            .shift(1)
            .rolling(3)
            .sum()
        )
        
        # Rain deviation from monthly normal
        monthly_normal = df.groupby(["district", "month"])["monthly_rain_sum"].transform("mean")
        df["rain_dev"] = df["monthly_rain_sum"] - monthly_normal
        
        # ============ NDVI FEATURES ============
        # NDVI lag
        df["ndvi_lag_1"] = (
            df.groupby(["commodity", "district"])["monthly_ndvi_mean"]
            .shift(1)
        )
        
        # NDVI trend (difference from 3 months ago)
        df["ndvi_trend_3"] = (
            df.groupby(["commodity", "district"])["monthly_ndvi_mean"].transform(lambda x: x - x.shift(3))
        )
        
        # ============ SEASONALITY ============
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
        
        # ============ ADDITIONAL FEATURES (Model compatibility) ============
        # Create aliases for features the model expects with different names
        df["momentum_1"] = df["price_mom_1"]  # Alias
        df["momentum_3"] = df["price_mom_3"]  # Alias
        df["rain_anomaly"] = df["rain_dev"]  # Alias
        df["ndvi_momentum_3"] = df["ndvi_trend_3"]  # Alias
        
        # ============ CROP HORIZON ============
        df["horizon"] = df["commodity"].map(self.crop_horizon)
        
        # ============ ENCODING ============
        # Normalize district names before encoding (encoder was trained on normalized lowercase names)
        df["district_enc"] = self.district_encoder.transform(
            df["district"].apply(normalize_district_name)
        )
        df["commodity_enc"] = self.commodity_encoder.transform(df["commodity"])
        
        return df
    
    
    def predict(
        self,
        commodity: str,
        district: str,
        current_price: float,
        historical_data: pd.DataFrame,
        month: int,
        year: int,
        monthly_rain_sum: float,
        monthly_rain_mean: float,
        monthly_ndvi_mean: float,
        days_traded: int = 20
    ) -> Dict:
        """
        Generate harvest-window price prediction for a specific crop-district-month.
        
        Args:
            commodity: Crop name (e.g., "Garlic", "Wheat")
            district: District name (e.g., "Ahmedabad", "Rajkot")
            current_price: Current month modal price (₹/quintal)
            historical_data: DataFrame with past 12+ months of data for the commodity-district
            month: Current month (1-12)
            year: Current year
            monthly_rain_sum: Total monthly rainfall (mm)
            monthly_rain_mean: Average daily rainfall (mm)
            monthly_ndvi_mean: Mean NDVI for the month
            days_traded: Number of trading days in the month
            
        Returns:
            Dictionary with prediction results
        """
        
        # Normalize district name (encoder was trained on normalized lowercase names)
        district = normalize_district_name(district)
        
        # Validate commodity
        if commodity not in self.crop_horizon:
            available = ", ".join(sorted(self.crop_horizon.keys()))
            raise ValueError(f"Commodity '{commodity}' not supported. Available: {available}")
        
        # Get crop-specific horizon
        horizon = self.crop_horizon[commodity]
        
        # Build current month row
        current_row = pd.DataFrame([{
            "district": district,
            "commodity": commodity,
            "year": year,
            "month": month,
            "date": pd.to_datetime(f"{year}-{month:02d}-01"),
            "monthly_mean_price": current_price,
            "days_traded": days_traded,
            "monthly_rain_sum": monthly_rain_sum,
            "monthly_rain_mean": monthly_rain_mean,
            "monthly_ndvi_mean": monthly_ndvi_mean
        }])
        
        # Combine with historical data
        # Ensure historical district names are also normalized for consistent groupby
        historical_data = historical_data.copy()
        if "district" in historical_data.columns:
            historical_data["district"] = historical_data["district"].apply(normalize_district_name)
        full_data = pd.concat([historical_data, current_row], ignore_index=True)
        full_data = full_data.sort_values("date").reset_index(drop=True)
        
        # Engineer features
        full_data = self.engineer_features(full_data)
        
        # Get latest row (current month with features)
        latest = full_data.iloc[[-1]].copy()
        
        # Prepare features for model
        X = latest[self.feature_columns]
        
        # Check for missing features
        if X.isnull().any().any():
            missing_cols = X.columns[X.isnull().any()].tolist()
            raise ValueError(f"Missing feature values: {missing_cols}. Need at least 12 months of history.")
        
        # Predict log return
        predicted_return = self.model.predict(X)[0]
        
        # Convert to price
        predicted_harvest_price = current_price * np.exp(predicted_return)
        
        # Calculate harvest window dates
        harvest_month = month + horizon
        harvest_year = year
        if harvest_month > 12:
            harvest_month -= 12
            harvest_year += 1
        
        harvest_start = datetime(harvest_year, harvest_month, 1)
        
        # Build result
        result = {
            "commodity": commodity,
            "district": district,
            "current_month": f"{year}-{month:02d}",
            "current_price": round(current_price, 2),
            "growth_horizon_months": horizon,
            "harvest_window_start": harvest_start.strftime("%Y-%m"),
            "predicted_harvest_price": round(predicted_harvest_price, 2),
            "expected_return_percent": round(predicted_return * 100, 2),
            "absolute_change": round(predicted_harvest_price - current_price, 2),
            "model_type": self.metadata["model_type"],
            "prediction_timestamp": datetime.utcnow().isoformat()
        }
        
        return result
    
    
    def predict_multiple_crops(
        self,
        district: str,
        crop_data: List[Dict],
        month: int,
        year: int,
        historical_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate predictions for multiple crops in a district.
        
        Useful for helping farmers decide which crop to sow.
        
        Args:
            district: District name
            crop_data: List of dicts with keys: commodity, current_price, rain_sum, rain_mean, ndvi_mean
            month: Current month
            year: Current year
            historical_data: Historical data for all crops in the district
            
        Returns:
            DataFrame sorted by expected return (descending)
        """
        results = []
        
        for crop in crop_data:
            try:
                # Filter historical data for this crop
                crop_history = historical_data[
                    (historical_data["commodity"] == crop["commodity"]) &
                    (historical_data["district"] == district)
                ].copy()
                
                prediction = self.predict(
                    commodity=crop["commodity"],
                    district=district,
                    current_price=crop["current_price"],
                    historical_data=crop_history,
                    month=month,
                    year=year,
                    monthly_rain_sum=crop.get("monthly_rain_sum", 0),
                    monthly_rain_mean=crop.get("monthly_rain_mean", 0),
                    monthly_ndvi_mean=crop.get("monthly_ndvi_mean", 0.5)
                )
                
                results.append(prediction)
                
            except Exception as e:
                print(f"⚠ Failed to predict {crop['commodity']}: {e}")
                continue
        
        # Convert to DataFrame and sort by expected return
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values("expected_return_percent", ascending=False)
        
        return df_results
    
    
    def get_supported_crops(self) -> List[str]:
        """Get list of all supported crop names."""
        return sorted(self.crop_horizon.keys())
    
    
    def get_crop_horizon(self, commodity: str) -> int:
        """Get growth horizon for a specific crop."""
        return self.crop_horizon.get(commodity, None)


# ============ EXAMPLE USAGE ============
if __name__ == "__main__":
    
    # Initialize predictor
    predictor = CropPricePredictor()
    
    print("\n📋 Supported Crops:")
    print(predictor.get_supported_crops()[:10], "...")
    
    print("\n🌾 Crop Growth Horizons:")
    for crop in ["Garlic", "Wheat", "Cabbage", "Cotton", "Tomato"]:
        print(f"  {crop}: {predictor.get_crop_horizon(crop)} months")
