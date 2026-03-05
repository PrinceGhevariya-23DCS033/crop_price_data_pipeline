"""
FastAPI Backend for Crop Price Prediction
Gujarat Crop Price Forecasting System

Deployed on Hugging Face Spaces using Docker.
Used by React frontend deployed on Vercel.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cached_fetcher import CachedDataFetcher
from src.inference import CropPricePredictor
from src.config import DISTRICT_COORDS


# ============ PYDANTIC MODELS ============

class PredictionRequest(BaseModel):
    """Request model for crop price prediction."""
    commodity: str = Field(..., description="Crop name (e.g., 'Wheat', 'Cotton')")
    district: str = Field(..., description="District name (e.g., 'Ahmedabad')")
    year: int = Field(..., ge=2005, le=2030, description="Year")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")


class PredictionResponse(BaseModel):
    """Response model for prediction."""
    success: bool
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
    environmental_data: dict
    recommendation: str


class CacheStatusResponse(BaseModel):
    """Response for cache status."""
    cache_available: bool
    cache_current: bool
    last_updated: Optional[str]
    update_period: Optional[str]
    total_entries: dict
    coverage: dict


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool
    error: str
    detail: Optional[str]


# ============ INITIALIZE APP ============

app = FastAPI(
    title="Gujarat Crop Price Forecasting API",
    description="FastAPI backend for crop price predictions using monthly cached data",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - Allow Vercel frontend (update with your Vercel domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local React dev
        "http://localhost:5173",  # Local Vite dev
        "https://*.vercel.app",   # All Vercel preview deployments
        "https://your-app.vercel.app",  # Replace with your production domain
        "*"  # Remove this in production, specify exact domains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
try:
    predictor = CropPricePredictor(model_dir="production_model")
    data_fetcher = CachedDataFetcher(
        cache_dir="monthly_cache",
        use_api_fallback=False  # API-only mode, no external calls
    )
    print("✓ Model and cache loaded successfully")
except Exception as e:
    print(f"❌ Initialization error: {e}")
    predictor = None
    data_fetcher = None


# ============ HELPER FUNCTIONS ============

def load_historical_data(commodity: str, district: str, months_back: int = 18):
    """Load historical data for predictions."""
    import pandas as pd
    from src.config import normalize_district_name
    
    commodity_file = commodity.lower().replace(" ", "_") + "_final.csv"
    file_path = os.path.join("processed", commodity_file)
    
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"])
    
    # Filter for district
    normalized_district = normalize_district_name(district)
    if "district" in df.columns:
        df["district_norm"] = df["district"].apply(normalize_district_name)
        df = df[df["district_norm"] == normalized_district].copy()
    
    if df.empty:
        return None
    
    df = df.sort_values("date").tail(months_back)
    return df


# ============ API ENDPOINTS ============

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Gujarat Crop Price Forecasting API",
        "version": "2.0.0",
        "deployment": "Hugging Face Spaces",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    cache_status = data_fetcher.get_cache_status() if data_fetcher else {}
    
    return {
        "status": "healthy" if (predictor and data_fetcher) else "unhealthy",
        "model_loaded": predictor is not None,
        "cache_loaded": data_fetcher is not None,
        "cache_current": cache_status.get("cache_current", False),
        "last_cache_update": cache_status.get("last_updated"),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/crops", response_model=List[str])
async def get_crops():
    """Get list of all supported crops."""
    if not predictor:
        raise HTTPException(status_code=503, detail="Model not available")
    
    return sorted(predictor.get_supported_crops())


@app.get("/api/districts", response_model=List[str])
async def get_districts():
    """Get list of all supported districts."""
    return sorted(list(DISTRICT_COORDS.keys()))


@app.get("/api/cache-status", response_model=CacheStatusResponse)
async def get_cache_status():
    """Get cache status and metadata."""
    if not data_fetcher:
        raise HTTPException(status_code=503, detail="Data fetcher not available")
    
    status = data_fetcher.get_cache_status()
    return CacheStatusResponse(**status)


@app.post("/api/predict", response_model=PredictionResponse)
async def predict_price(request: PredictionRequest):
    """
    Predict harvest-window price for a crop.
    
    This is the main endpoint used by the React frontend.
    """
    if not predictor or not data_fetcher:
        raise HTTPException(status_code=503, detail="Service not available")
    
    try:
        # Get all data from cache
        data = data_fetcher.get_all_data(
            commodity=request.commodity,
            district=request.district,
            year=request.year,
            month=request.month
        )
        
        # Check if we have current price
        if data["current_price"] is None or data["current_price"] == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No price data available for {request.commodity} in {request.district}"
            )
        
        # Load historical data
        historical_data = load_historical_data(
            request.commodity,
            request.district,
            months_back=18
        )
        
        if historical_data is None or historical_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data for {request.commodity} in {request.district}"
            )
        
        # Make prediction
        result = predictor.predict(
            commodity=request.commodity,
            district=request.district,
            current_price=data["current_price"],
            historical_data=historical_data,
            month=request.month,
            year=request.year,
            monthly_rain_sum=data["monthly_rain_sum"],
            monthly_rain_mean=data["monthly_rain_mean"],
            monthly_ndvi_mean=data["monthly_ndvi_mean"],
            days_traded=data["days_traded"]
        )
        
        # Add environmental data
        environmental_data = {
            "rainfall_sum_mm": data["monthly_rain_sum"],
            "rainfall_mean_mm": data["monthly_rain_mean"],
            "ndvi": data["monthly_ndvi_mean"],
            "days_traded": data["days_traded"],
            "price_source": data["price_source"],
            "rainfall_source": data["rainfall_source"],
            "ndvi_source": data["ndvi_source"]
        }
        
        # Generate recommendation
        return_pct = result["expected_return_percent"]
        if return_pct > 10:
            recommendation = "POSITIVE - Strong expected returns suggest favorable market conditions"
        elif return_pct > 0:
            recommendation = "MODERATE - Modest price appreciation expected"
        else:
            recommendation = "CAUTION - Potential price decline, consider alternatives"
        
        # Build response
        return PredictionResponse(
            success=True,
            commodity=result["commodity"],
            district=result["district"],
            current_month=result["current_month"],
            current_price=result["current_price"],
            growth_horizon_months=result["growth_horizon_months"],
            harvest_window_start=result["harvest_window_start"],
            predicted_harvest_price=result["predicted_harvest_price"],
            expected_return_percent=result["expected_return_percent"],
            absolute_change=result["absolute_change"],
            model_type=result["model_type"],
            prediction_timestamp=result["prediction_timestamp"],
            environmental_data=environmental_data,
            recommendation=recommendation
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@app.get("/api/crop/{commodity}/info")
async def get_crop_info(commodity: str):
    """Get information about a specific crop."""
    if not predictor:
        raise HTTPException(status_code=503, detail="Model not available")
    
    horizon = predictor.get_crop_horizon(commodity)
    
    if horizon is None:
        raise HTTPException(
            status_code=404,
            detail=f"Crop '{commodity}' not found"
        )
    
    return {
        "commodity": commodity,
        "growth_horizon_months": horizon,
        "description": f"{commodity} takes approximately {horizon} months from sowing to harvest"
    }


# ============ ERROR HANDLERS ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return {
        "success": False,
        "error": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    return {
        "success": False,
        "error": "Internal server error",
        "detail": str(exc)
    }


# ============ STARTUP EVENT ============

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    print("=" * 70)
    print("Gujarat Crop Price Forecasting API")
    print("=" * 70)
    print(f"Model loaded: {predictor is not None}")
    print(f"Cache loaded: {data_fetcher is not None}")
    
    if data_fetcher:
        status = data_fetcher.get_cache_status()
        print(f"Cache entries: {status['entries']}")
        print(f"Last updated: {status['last_updated']}")
        print(f"Cache current: {status['cache_current']}")
    
    print("=" * 70)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=7860,
        reload=False
    )
