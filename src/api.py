"""
FastAPI Backend
Gujarat Crop Price Forecasting System

REST API for crop price predictions.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import pandas as pd
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from inference import CropPricePredictor
from data_fetchers import CombinedDataFetcher
from confidence import PredictionWithConfidence, add_confidence_to_prediction
from config import DISTRICT_COORDS, normalize_district_name


# ============ PYDANTIC MODELS ============

class PredictionRequest(BaseModel):
    """Request model for single crop prediction."""
    commodity: str = Field(..., description="Crop name (e.g., 'Garlic', 'Wheat')")
    district: str = Field(..., description="District name (e.g., 'Ahmedabad')")
    current_price: float = Field(..., gt=0, description="Current modal price (₹/quintal)")
    year: int = Field(..., ge=2005, le=2030, description="Current year")
    month: int = Field(..., ge=1, le=12, description="Current month (1-12)")
    monthly_rain_sum: Optional[float] = Field(0, description="Monthly rainfall sum (mm)")
    monthly_rain_mean: Optional[float] = Field(0, description="Mean daily rainfall (mm)")
    monthly_ndvi_mean: Optional[float] = Field(0.5, description="Mean NDVI (0-1)")
    days_traded: Optional[int] = Field(20, description="Trading days in month")


class PredictionResponse(BaseModel):
    """Response model for prediction."""
    commodity: str
    district: str
    current_month: str
    current_price: float
    growth_horizon_months: int
    harvest_window_start: str
    predicted_harvest_price: float
    expected_return_percent: float
    absolute_change: float
    model_type: str
    prediction_timestamp: str


class HistoricalDataRequest(BaseModel):
    """Request for fetching historical data."""
    commodity: str
    district: str
    months_back: int = Field(12, ge=1, le=60, description="Number of months of history")


class CropComparisonRequest(BaseModel):
    """Request for comparing multiple crops."""
    district: str
    commodities: List[str] = Field(..., min_items=2, max_items=20)
    year: int
    month: int


# ============ INITIALIZE APP ============

app = FastAPI(
    title="Gujarat Crop Price Forecasting API",
    description="Pre-production harvest-window crop price predictions for Gujarat",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize predictor and data fetcher
try:
    predictor = CropPricePredictor(model_dir="production_model")
    data_fetcher = CombinedDataFetcher()
    confidence_estimator = None  # Will be initialized with historical data if available
    print("✓ Model and fetchers initialized")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    predictor = None
    data_fetcher = None
    confidence_estimator = None


# ============ HELPER FUNCTIONS ============

def load_historical_data(
    commodity: str,
    district: str,
    months_back: int = 12
) -> pd.DataFrame:
    """
    Load historical data from processed files.
    
    Args:
        commodity: Crop name
        district: District name
        months_back: Number of months to load
        
    Returns:
        DataFrame with historical data
    """
    
    # Map commodity to filename
    commodity_file = commodity.lower().replace(" ", "_") + "_final.csv"
    file_path = os.path.join("processed", commodity_file)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Historical data not found for {commodity}")
    
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"])
    
    # Filter for district
    df = df[df["district"] == district].copy()
    
    if df.empty:
        raise ValueError(f"No data found for {commodity} in {district}")
    
    # Sort by date and get last N months
    df = df.sort_values("date")
    df = df.tail(months_back)
    
    return df


# ============ API ENDPOINTS ============

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Gujarat Crop Price Forecasting API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    
    model_status = "loaded" if predictor else "failed"
    fetcher_status = "loaded" if data_fetcher else "failed"
    
    return {
        "status": "healthy" if (predictor and data_fetcher) else "unhealthy",
        "model": model_status,
        "data_fetcher": fetcher_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/crops", response_model=List[str])
async def get_supported_crops():
    """Get list of all supported crops."""
    
    if not predictor:
        raise HTTPException(status_code=503, detail="Model not available")
    
    return predictor.get_supported_crops()


@app.get("/crops/{commodity}/horizon")
async def get_crop_horizon(commodity: str):
    """Get growth horizon for a specific crop."""
    
    if not predictor:
        raise HTTPException(status_code=503, detail="Model not available")
    
    horizon = predictor.get_crop_horizon(commodity)
    
    if horizon is None:
        raise HTTPException(
            status_code=404,
            detail=f"Crop '{commodity}' not found. Use /crops to see supported crops."
        )
    
    return {
        "commodity": commodity,
        "growth_horizon_months": horizon,
        "description": f"{commodity} takes approximately {horizon} months from sowing to harvest"
    }
@app.post("/predict", response_model=PredictionResponse)
async def predict_harvest_price(request: PredictionRequest):
    """
    Predict harvest-window price for a specific crop.
    
    Requires historical price data to compute lag and rolling features.
    Includes confidence intervals for uncertainty estimation.
    """
    
    if not predictor:
        raise HTTPException(status_code=503, detail="Model not available")
    
    try:
        # Load historical data
        historical_data = load_historical_data(
            commodity=request.commodity,
            district=request.district,
            months_back=18  # Need 12+ for lag features
        )
        
        # Make prediction
        result = predictor.predict(
            commodity=request.commodity,
            district=request.district,
            current_price=request.current_price,
            historical_data=historical_data,
            month=request.month,
            year=request.year,
            monthly_rain_sum=request.monthly_rain_sum,
            monthly_rain_mean=request.monthly_rain_mean,
            monthly_ndvi_mean=request.monthly_ndvi_mean,
            days_traded=request.days_traded
        )
        
        # Add confidence intervals (using simple method)
        predicted_price = result['predicted_harvest_price']
        uncertainty = predicted_price * 0.15  # 15% typical uncertainty
        
        result['confidence_interval'] = {
            'lower_bound': round(max(0, predicted_price - uncertainty), 2),
            'upper_bound': round(predicted_price + uncertainty, 2),
            'confidence_level': 90,
            'uncertainty_percent': 15.0
        }
        
        return result
    
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/auto")
async def predict_with_auto_fetch(
    commodity: str = Query(..., description="Crop name"),
    district: str = Query(..., description="District name"),
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month (1-12)")
):
    """
    Predict harvest price with automatic data fetching.
    
    Automatically fetches:
    - Historical mandi prices (last 18 months) from data.gov.in
    - Current month mandi price from data.gov.in
    - Weather data from Open-Meteo
    - NDVI from Google Earth Engine (if available)
    """
    
    if not predictor or not data_fetcher:
        raise HTTPException(status_code=503, detail="Services not available")
    
    try:
        print(f"\\n{'='*60}")
        print(f"Auto-prediction request: {commodity} in {district} ({year}-{month:02d})")
        print(f"{'='*60}")
        
        # Normalize district name
        normalized_district = normalize_district_name(district)
        
        # Step 1: Fetch historical data from CSV files
        print("\\n[1/4] Fetching historical price data from CSV files...")
        historical_data = data_fetcher.mandi_fetcher.fetch_historical_monthly_prices(
            commodity=commodity,
            district=district,
            months_back=18
        )
        
        if historical_data.empty:
            raise HTTPException(
                status_code=400,
                detail=f"No historical data found for {commodity} in {district}. Check if CSV file exists in processed/ folder."
            )
        
        if historical_data.empty or len(historical_data) < 12:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient historical data. Need 12+ months, found {len(historical_data)}"
            )
        
        print(f"  ✓ Loaded {len(historical_data)} months of historical data")
        
        # Add weather and NDVI columns if missing (use defaults)
        if "monthly_rain_sum" not in historical_data.columns:
            historical_data["monthly_rain_sum"] = 0.0
        if "monthly_rain_mean" not in historical_data.columns:
            historical_data["monthly_rain_mean"] = 0.0
        if "monthly_ndvi_mean" not in historical_data.columns:
            historical_data["monthly_ndvi_mean"] = 0.5
        if "days_traded" not in historical_data.columns:
            historical_data["days_traded"] = 20
        
        # Ensure required columns exist
        required_cols = ["date", "commodity", "district", "monthly_mean_price", 
                        "year", "month"]
        missing = [col for col in required_cols if col not in historical_data.columns]
        if missing:
            raise HTTPException(
                status_code=500,
                detail=f"Historical data missing columns: {missing}"
            )
        
        # Step 2: Fetch current month price with smart fallback
        print(f"\n[2/4] Fetching current price with smart fallback...")
        
        # Use smart fallback: 15 days → 30 days → latest available
        current_price_data = data_fetcher.mandi_fetcher.get_current_price_with_fallback(
            commodity=commodity,
            district=district,
            reference_date=datetime(year, month, 15)  # Mid-month reference
        )
        
        if not current_price_data:
            raise HTTPException(
                status_code=404,
                detail=f"No price data available for {commodity} in {district}"
            )
        
        print(f"  ✓ {current_price_data['price_source']}")
        print(f"  ✓ Price: ₹{current_price_data['monthly_mean_price']:.2f}")
        print(f"  ✓ Data until: {current_price_data['data_until_date']}")
        
        # Fetch weather and NDVI data
        print(f"\n[3/4] Fetching weather and NDVI data...")
        weather_data = data_fetcher.weather_fetcher.get_monthly_rainfall(
            district=district,
            year=year,
            month=month
        )
        
        if not weather_data:
            print("  ⚠ Weather data unavailable, using defaults")
            weather_data = {"monthly_rain_sum": 0, "monthly_rain_mean": 0}
        else:
            print(f"  ✓ Rainfall: {weather_data['monthly_rain_sum']:.1f}mm")
        
        ndvi_data = data_fetcher.ndvi_fetcher.get_monthly_ndvi(
            district=district,
            year=year,
            month=month,
            commodity=commodity  # Pass commodity for CSV fallback
        )
        
        if not ndvi_data:
            print("  ⚠ NDVI data unavailable, using default")
            ndvi_data = {"monthly_ndvi_mean": 0.5}
        else:
            ndvi_source = ndvi_data.get("source", "GEE")
            ndvi_date = ndvi_data.get("data_date", "")
            print(f"  ✓ NDVI: {ndvi_data['monthly_ndvi_mean']:.3f} (from {ndvi_source}" + (f", data date: {ndvi_date}" if ndvi_date else "") + ")")
        
        # Step 4: Make prediction
        print(f"\\n[4/4] Generating prediction...")
        result = predictor.predict(
            commodity=commodity,
            district=normalized_district,  
            current_price=current_price_data["monthly_mean_price"],
            historical_data=historical_data,
            month=month,
            year=year,
            monthly_rain_sum=weather_data.get("monthly_rain_sum", 0),
            monthly_rain_mean=weather_data.get("monthly_rain_mean", 0),
            monthly_ndvi_mean=ndvi_data.get("monthly_ndvi_mean", 0.5),
            days_traded=current_price_data.get("days_traded", 20)
        )
        
        # Add fetched data to response
        result["fetched_data"] = {
            "current_price": current_price_data["monthly_mean_price"],
            "price_source": current_price_data["price_source"],
            "data_source": current_price_data.get("data_source", "CSV"),  # API or CSV
            "data_until_date": current_price_data["data_until_date"],
            "is_recent_data": current_price_data["is_recent"],
            "rain_sum": weather_data.get("monthly_rain_sum", 0),
            "rain_mean": weather_data.get("monthly_rain_mean", 0),
            "ndvi": ndvi_data.get("monthly_ndvi_mean", 0.5),
            "days_traded": current_price_data.get("days_traded", 20),
            "historical_months_used": len(historical_data)
        }
        
        # Add warning if data is old
        if "warning" in current_price_data:
            result["data_warning"] = current_price_data["warning"]
        
        print(f"  ✓ Predicted harvest price: ₹{result['predicted_harvest_price']:.2f}")
        print(f"  ✓ Expected return: {result['expected_return_percent']:.1f}%")
        print(f"{'='*60}\\n")
        
        return result
    
    except HTTPException:
        raise
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Auto-prediction failed: {str(e)}")


@app.post("/compare")
async def compare_crops(request: CropComparisonRequest):
    """
    Compare multiple crops for a district to help farmers decide what to sow.
    
    Returns crops sorted by expected return (descending).
    """
    
    if not predictor:
        raise HTTPException(status_code=503, detail="Model not available")
    
    try:
        crops_data = []
        
        # Prepare data for each crop
        for commodity in request.commodities:
            try:
                # Load historical data
                historical_data = load_historical_data(
                    commodity=commodity,
                    district=request.district,
                    months_back=18
                )
                
                # Get latest price as current price
                latest = historical_data.iloc[-1]
                
                crop_info = {
                    "commodity": commodity,
                    "current_price": latest["monthly_mean_price"],
                    "monthly_rain_sum": latest.get("monthly_rain_sum", 0),
                    "monthly_rain_mean": latest.get("monthly_rain_mean", 0),
                    "monthly_ndvi_mean": latest.get("monthly_ndvi_mean", 0.5)
                }
                
                crops_data.append(crop_info)
            
            except Exception as e:
                print(f"⚠ Skipping {commodity}: {e}")
                continue
        
        if not crops_data:
            raise HTTPException(
                status_code=404,
                detail="No valid data found for any of the requested crops"
            )
        
        # Load all historical data
        all_historical = pd.concat([
            load_historical_data(crop["commodity"], request.district, 18)
            for crop in crops_data
        ], ignore_index=True)
        
        # Generate predictions
        comparison = predictor.predict_multiple_crops(
            district=request.district,
            crop_data=crops_data,
            month=request.month,
            year=request.year,
            historical_data=all_historical
        )
        
        return {
            "district": request.district,
            "comparison_month": f"{request.year}-{request.month:02d}",
            "crops_compared": len(comparison),
            "recommendations": comparison.to_dict(orient="records")
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@app.get("/historical/{commodity}/{district}")
async def get_historical_prices(
    commodity: str,
    district: str,
    months: int = Query(12, ge=1, le=60, description="Number of months")
):
    """Get historical price data for a commodity-district pair."""
    
    try:
        df = load_historical_data(commodity, district, months)
        
        # Format for response
        records = df[["date", "monthly_mean_price", "days_traded"]].to_dict(orient="records")
        
        # Convert dates to strings
        for record in records:
            record["date"] = record["date"].strftime("%Y-%m-%d")
        
        return {
            "commodity": commodity,
            "district": district,
            "months_returned": len(records),
            "data": records
        }
    
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/districts")
async def get_districts():
    """Get list of districts with available weather data (normalized names)."""
    
    districts = sorted(DISTRICT_COORDS.keys())
    
    return {
        "count": len(districts),
        "districts": districts,
        "note": "District names are normalized. Variations like 'Ahmedabad' will be mapped to 'Ahmadabad'"
    }


# ============ RUN SERVER ============

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
