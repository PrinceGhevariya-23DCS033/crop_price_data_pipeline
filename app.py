"""
Hugging Face Gradio App
Gujarat Crop Price Forecasting System

Fast predictions using monthly cached data.
Optimized for Hugging Face Spaces deployment.
"""

import gradio as gr
import pandas as pd
import sys
import os
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.inference import CropPricePredictor
from src.cached_fetcher import CachedDataFetcher
from src.config import DISTRICT_COORDS, normalize_district_name


# ============ INITIALIZE SYSTEM ============

print("🚀 Initializing Gujarat Crop Price Forecasting System...")

# Initialize predictor
try:
    predictor = CropPricePredictor(model_dir="production_model")
    print("✓ Model loaded")
except Exception as e:
    print(f"❌ Model loading failed: {e}")
    predictor = None

# Initialize cached data fetcher (cache-only mode for HF)
try:
    data_fetcher = CachedDataFetcher(
        cache_dir="monthly_cache",
        use_api_fallback=False  # Disable API calls on HF for speed
    )
    cache_status = data_fetcher.get_cache_status()
    print(f"✓ Cache loaded: {cache_status['entries']['prices']} price entries")
    print(f"  Last updated: {cache_status['last_updated']}")
except Exception as e:
    print(f"⚠️  Cache initialization warning: {e}")
    data_fetcher = None

# Get available crops and districts
AVAILABLE_CROPS = sorted(predictor.get_supported_crops()) if predictor else []
AVAILABLE_DISTRICTS = sorted(list(DISTRICT_COORDS.keys()))


# ============ HELPER FUNCTIONS ============

def load_historical_data(commodity: str, district: str, months_back: int = 18):
    """Load historical data for commodity-district."""
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
    
    # Sort by date and get last N months
    df = df.sort_values("date").tail(months_back)
    return df


# ============ PREDICTION FUNCTION ============

def predict_crop_price(commodity: str, district: str):
    """
    Make crop price prediction using cached data.
    
    Args:
        commodity: Crop name
        district: District name
        
    Returns:
        Formatted prediction results
    """
    
    if not predictor:
        return "❌ Model not loaded. Please contact administrator."
    
    if not data_fetcher:
        return "❌ Data fetcher not available. Please contact administrator."
    
    try:
        # Get current date
        now = datetime.now()
        year = now.year
        month = now.month
        
        # Get all data from cache
        data = data_fetcher.get_all_data(
            commodity=commodity,
            district=district,
            year=year,
            month=month
        )
        
        # Check if we have current price
        if data["current_price"] is None or data["current_price"] == 0:
            return f"""
            ❌ **No Price Data Available**
            
            Unfortunately, we don't have current price data for **{commodity}** in **{district}**.
            
            This could be because:
            - The crop is not currently traded in this district
            - The monthly cache needs to be updated
            - No historical data exists for this combination
            
            Please try:
            - A different district where this crop is commonly grown
            - A different crop for this district
            """
        
        # Load historical data
        historical_data = load_historical_data(commodity, district, months_back=18)
        
        if historical_data is None or historical_data.empty:
            return f"""
            ❌ **No Historical Data Available**
            
            Cannot make prediction for **{commodity}** in **{district}** without historical data.
            """
        
        # Make prediction
        result = predictor.predict(
            commodity=commodity,
            district=district,
            current_price=data["current_price"],
            historical_data=historical_data,
            month=month,
            year=year,
            monthly_rain_sum=data["monthly_rain_sum"],
            monthly_rain_mean=data["monthly_rain_mean"],
            monthly_ndvi_mean=data["monthly_ndvi_mean"],
            days_traded=data["days_traded"]
        )
        
        # Format output
        output = f"""
        # 📊 Crop Price Prediction
        
        ## Crop Information
        - **Commodity:** {result['commodity']}
        - **District:** {result['district']}
        - **Growth Horizon:** {result['growth_horizon_months']} months
        
        ## Current Status ({result['current_month']})
        - **Current Price:** ₹{result['current_price']:.2f} per quintal
        - **Data Source:** {data['price_source']}
        
        ## Environmental Conditions
        - **Rainfall (Current Month):** {data['monthly_rain_sum']:.1f} mm (Avg: {data['monthly_rain_mean']:.1f} mm/day)
        - **NDVI (Vegetation Index):** {data['monthly_ndvi_mean']:.4f}
        - **Trading Days:** {data['days_traded']} days
        
        ---
        
        ## 🎯 Harvest Window Prediction
        
        ### {result['harvest_window_start']}
        
        **Predicted Harvest Price:** ₹{result['predicted_harvest_price']:.2f} per quintal
        
        **Expected Return:** {result['expected_return_percent']:+.2f}%
        
        **Absolute Change:** {result['absolute_change']:+.2f} ₹/quintal
        
        ---
        
        ## 📈 Recommendation
        
        """
        
        if result['expected_return_percent'] > 10:
            output += f"""
            ✅ **POSITIVE OUTLOOK**
            
            Strong expected returns of **{result['expected_return_percent']:.1f}%** suggest favorable market conditions at harvest.
            Consider this crop for cultivation.
            """
        elif result['expected_return_percent'] > 0:
            output += f"""
            ⚠️ **MODERATE OUTLOOK**
            
            Expected returns of **{result['expected_return_percent']:.1f}%** show modest price appreciation.
            Evaluate other factors like input costs and market demand.
            """
        else:
            output += f"""
            ⚠️ **CAUTION**
            
            Expected returns of **{result['expected_return_percent']:.1f}%** indicate potential price decline.
            Consider alternative crops or review cultivation strategy.
            """
        
        output += f"""
        
        ---
        
        ## ℹ️ About This Prediction
        
        - **Model Type:** {result['model_type']}
        - **Prediction Made:** {result['prediction_timestamp']}
        - **Data Period:** {cache_status['update_period']}
        
        *Note: This is a forecast based on historical patterns and current conditions. 
        Actual prices may vary due to market dynamics, policy changes, and unforeseen events.*
        """
        
        return output
    
    except Exception as e:
        return f"""
        ❌ **Prediction Error**
        
        An error occurred while making the prediction:
        
        ```
        {str(e)}
        ```
        
        Please try again or contact support.
        """


def get_cache_info():
    """Get cache information for display."""
    if not data_fetcher:
        return "Cache information not available."
    
    try:
        status = data_fetcher.get_cache_status()
        
        info = f"""
        # 📦 Data Cache Status
        
        - **Last Updated:** {status['last_updated'] or 'Never'}
        - **Data Period:** {status['update_period'] or 'N/A'}
        - **Cache Current:** {'✅ Yes' if status['cache_current'] else '⚠️ Outdated'}
        
        ## Coverage
        - **Price Entries:** {status['entries']['prices']}
        - **Rainfall Entries:** {status['entries']['rainfall']}
        - **NDVI Entries:** {status['entries']['ndvi']}
        - **Commodities:** {status['coverage']['commodities']}
        - **Districts:** {status['coverage']['districts']}
        
        ---
        
        *Data is updated monthly between 20-25th when NDVI satellite data becomes available.*
        """
        
        return info
    
    except Exception as e:
        return f"Error getting cache info: {e}"


# ============ GRADIO INTERFACE ============

def create_interface():
    """Create Gradio interface."""
    
    with gr.Blocks(title="Gujarat Crop Price Forecasting", theme=gr.themes.Soft()) as app:
        
        gr.Markdown("""
        # 🌾 Gujarat Crop Price Forecasting System
        
        Predict harvest-window prices for crops in Gujarat using ML models trained on historical data, 
        weather patterns, and satellite vegetation indices (NDVI).
        
        **How it works:** Select a crop and district to get a price forecast for the harvest window 
        (based on the crop's growth cycle). The system uses monthly cached data for fast predictions.
        """)
        
        with gr.Tab("Price Prediction"):
            gr.Markdown("### Make a Prediction")
            
            with gr.Row():
                with gr.Column():
                    commodity_input = gr.Dropdown(
                        choices=AVAILABLE_CROPS,
                        label="Select Crop",
                        info="Choose the crop you want to predict"
                    )
                    
                    district_input = gr.Dropdown(
                        choices=AVAILABLE_DISTRICTS,
                        label="Select District",
                        info="Choose the district for cultivation"
                    )
                    
                    predict_btn = gr.Button("🔮 Predict Harvest Price", variant="primary", size="lg")
                
                with gr.Column():
                    gr.Markdown("""
                    ### Quick Tips
                    
                    1. **Choose crops** commonly grown in your selected district for best results
                    2. **Predictions** are based on the crop's natural growth cycle
                    3. **Green returns** (>10%) suggest favorable market conditions
                    4. **Consider** input costs and local market factors in your decision
                    
                    *Data is updated monthly with latest prices, rainfall, and NDVI.*
                    """)
            
            output = gr.Markdown(label="Prediction Results")
            
            predict_btn.click(
                fn=predict_crop_price,
                inputs=[commodity_input, district_input],
                outputs=output
            )
            
            gr.Markdown("""
            ---
            
            ### Example Combinations
            
            Try these popular crop-district combinations:
            - **Wheat** in Ahmedabad, Mehsana, or Banaskantha
            - **Cotton** in Rajkot, Surendranagar, or Bhavnagar
            - **Groundnut** in Junagadh, Rajkot, or Jamnagar
            - **Onion** in Ahmedabad, Anand, or Kheda
            """)
        
        with gr.Tab("Data Status"):
            gr.Markdown("### Current Data Cache Status")
            
            cache_info_output = gr.Markdown(value=get_cache_info())
            
            refresh_btn = gr.Button("🔄 Refresh Status")
            refresh_btn.click(
                fn=get_cache_info,
                outputs=cache_info_output
            )
            
            gr.Markdown("""
            ---
            
            ### About the Data
            
            Our predictions are powered by three key data sources:
            
            1. **Mandi Prices** - Historical price data from agricultural markets across Gujarat
            2. **Rainfall Data** - Monthly rainfall from Open-Meteo weather API
            3. **NDVI (Vegetation Index)** - Satellite-based vegetation health from MODIS
            
            The cache is updated monthly (20-25th) when new NDVI data becomes available. 
            This ensures predictions are based on the latest conditions while maintaining fast response times.
            """)
        
        with gr.Tab("About"):
            gr.Markdown("""
            # About Gujarat Crop Price Forecasting System
            
            ## Overview
            
            This system helps farmers and agricultural planners make informed cultivation decisions 
            by predicting harvest-window prices for crops in Gujarat.
            
            ## How It Works
            
            1. **Historical Patterns** - Analyzes years of price data, weather, and crop cycles
            2. **Current Conditions** - Uses latest prices, rainfall, and vegetation health (NDVI)
            3. **ML Models** - Trained models predict prices at harvest time based on growth horizons
            4. **Fast Predictions** - Monthly cached data ensures sub-second response times
            
            ## Features
            
            - ✅ 45+ crops supported
            - ✅ 33 districts covered
            - ✅ Growth cycle aware predictions
            - ✅ Real environmental factors (rainfall, NDVI)
            - ✅ Updated monthly with latest data
            
            ## Limitations
            
            - Predictions are forecasts, not guarantees
            - Market prices can be affected by unforeseen events
            - Data updated monthly (not real-time)
            - Best results for crops commonly grown in the selected district
            
            ## Data Sources
            
            - **Mandi Prices:** data.gov.in (Agmarknet API)
            - **Weather:** Open-Meteo API
            - **NDVI:** Google Earth Engine (MODIS satellite)
            
            ## Version
            
            - **Version:** 1.0.0
            - **Last Model Update:** February 2024
            - **Cache Update Schedule:** Monthly (20-25th)
            
            ---
            
            *Developed for agricultural decision support in Gujarat*
            """)
    
    return app


# ============ LAUNCH APP ============

if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
