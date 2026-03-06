"""
Configuration Module
Gujarat Crop Price Forecasting System

Centralized configuration management.
"""

import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============ DISTRICT NORMALIZATION ============

def normalize_district_name(name: str) -> str:
    """
    Normalize district name to match the format in district_latlon.csv.
    
    Based on the normalization logic from crop_price_v2_merge.ipynb.
    
    Args:
        name: District name in any format
        
    Returns:
        Normalized district name matching district_latlon.csv
    """
    normalized = (
        str(name)
        .lower()
        .replace(" ", "")
        .replace("(baroda)", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    )
    
    # Mandi API to district_latlon.csv mapping
    mandi_mapping = {
        "ahmedabad": "ahmadabad",
        "banaskanth": "banaskantha",
        "junagarh": "junagadh",
        "vadodara": "vadodara",
        "vadodarabaroda": "vadodara",
        "thedangs": "thedangs",
        "the dangs": "thedangs",
        "dangs": "thedangs",
        "gir somnath": "girsomnath",
        "girsomnath": "girsomnath",
        "devbhumi dwarka": "devbhumidwarka",
        "devbhumidwarka": "devbhumidwarka",
        "chhota udaipur": "chhotaudaipur",
        "chhotaudaipur": "chhotaudaipur",
        "panchmahals": "panchmahals",
        "panchmahal": "panchmahals",
        "sabarkantha": "sabarkantha",
        "mehsana": "mahesana",
        "mahesana": "mahesana",
        "kachchh": "kachchh",
        "kutch": "kachchh",
        "aravalli": "aravalli",
    }
    
    return mandi_mapping.get(normalized, normalized)


class Config:
    """Application configuration."""
    
    # Project paths
    BASE_DIR = Path(__file__).parent.parent
    MODEL_DIR = BASE_DIR / "production_model"
    PROCESSED_DIR = BASE_DIR / "processed"
    FINAL_DIR = BASE_DIR / "final"
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    API_RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"
    
    # External API Keys
    DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY")
    GEE_PROJECT_ID = os.getenv("GEE_PROJECT_ID")
    
    # Model Configuration
    MODEL_TYPE = "LightGBM"
    FEATURE_LAG_MONTHS = 12
    MIN_HISTORICAL_MONTHS = 18
    
    # Prediction Configuration
    DEFAULT_CONFIDENCE_LEVEL = 0.90
    DEFAULT_UNCERTAINTY_PERCENT = 15.0
    
    # API Rate Limiting
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_PERIOD = 60  # seconds
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS
    CORS_ORIGINS = ["*"]  # Change in production to specific domains
    
    # Cache TTL
    CACHE_TTL_SECONDS = 300  # 5 minutes
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        errors = []
        
        if not cls.DATA_GOV_API_KEY:
            errors.append("DATA_GOV_API_KEY not set in .env file")
        
        if not cls.MODEL_DIR.exists():
            errors.append(f"Model directory not found: {cls.MODEL_DIR}")
        
        if not cls.PROCESSED_DIR.exists():
            errors.append(f"Processed data directory not found: {cls.PROCESSED_DIR}")
        
        if errors:
            error_msg = "\n".join(f"  - {err}" for err in errors)
            raise RuntimeError(f"Configuration errors:\n{error_msg}")
        
        return True


# ============ LOAD DISTRICT COORDINATES FROM CSV ============

def load_district_coordinates():
    """
    Load district coordinates from district_latlon.csv.
    
    Returns:
        Dict mapping district name (in lowercase) to (latitude, longitude) tuple
    """
    csv_path = Path(__file__).parent.parent / "district_latlon.csv"
    
    if not csv_path.exists():
        print(f"⚠ Warning: District coordinates file not found: {csv_path}")
        return {}
    
    try:
        df = pd.read_csv(csv_path)
        
        # Create mapping with lowercase keys for easy lookup
        coords_dict = {}
        for _, row in df.iterrows():
            district_name = str(row['district']).lower()
            coords_dict[district_name] = (float(row['latitude']), float(row['longitude']))
        
        return coords_dict
    except Exception as e:
        print(f"⚠ Warning: Could not load district coordinates: {e}")
        return {}


# Load coordinates at module level
DISTRICT_COORDS = load_district_coordinates()


# ============ AGMARKNET API DISTRICT NAME MAPPING ============
# Maps the internal (normalized, lowercase) key → exact district string
# expected by data.gov.in Agmarknet filters[District] (case-sensitive).
AGMARKNET_DISTRICT_NAMES: dict = {
    "ahmadabad"      : "Ahmedabad",
    "amreli"         : "Amreli",
    "anand"          : "Anand",
    "aravalli"       : "Aravalli",
    "banaskantha"    : "Banaskantha",
    "bharuch"        : "Bharuch",
    "bhavnagar"      : "Bhavnagar",
    "botad"          : "Botad",
    "chhotaudaipur"  : "Chhota Udaipur",
    "dahod"          : "Dahod",
    "devbhumidwarka" : "Devbhumi Dwarka",
    "gandhinagar"    : "Gandhinagar",
    "girsomnath"     : "Gir Somnath",
    "jamnagar"       : "Jamnagar",
    "junagadh"       : "Junagadh",
    "kachchh"        : "Kutch",
    "kheda"          : "Kheda",
    "mahesana"       : "Mehsana",
    "mahisagar"      : "Mahisagar",
    "morbi"          : "Morbi",
    "narmada"        : "Narmada",
    "navsari"        : "Navsari",
    "panchmahals"    : "Panchmahal",
    "patan"          : "Patan",
    "porbandar"      : "Porbandar",
    "rajkot"         : "Rajkot",
    "sabarkantha"    : "Sabarkantha",
    "surat"          : "Surat",
    "surendranagar"  : "Surendranagar",
    "tapi"           : "Tapi",
    "thedangs"       : "The Dangs",
    "vadodara"       : "Vadodara",
    "valsad"         : "Valsad",
}


def agmarknet_district_name(district: str) -> str:
    """
    Return the exact district name expected by the data.gov.in Agmarknet API
    (filters[District] is case-sensitive on that endpoint).

    Falls back to Title-cased normalized name for any unknown district.
    """
    norm = normalize_district_name(district)
    return AGMARKNET_DISTRICT_NAMES.get(norm, norm.title())


# Crop growth horizons (months from sowing to harvest)
CROP_HORIZONS = {
    # Vegetables
    "Beans": 3, "Beetroot": 3, "Brinjal": 4, "Cabbage": 4,
    "Capsicum": 4, "Carrot": 3, "Cauliflower": 4, "Colacasia": 4,
    "Drumstick": 4, "Green Chilli": 4, "Green Peas": 3,
    "Leafy Vegetable": 2, "Onion Green": 2, "Peas Wet": 3,
    "Pumpkin": 4, "Raddish": 2, "Rajgir": 3,
    "Sweet Potato": 4, "Tinda": 3, "Tomato": 4, "Water Melon": 3,
    
    # Medium crops
    "Ajwan": 4, "Amaranthus": 3, "Castor Seed": 6,
    "Chili Red": 5, "Dry Chillies": 5, "Garlic": 6,
    "Ground Nut Seed": 5, "Groundnut": 5, "Guar": 4,
    "Maize": 4, "Methi Seeds": 4, "Moath Dal": 4,
    "Mustard": 5, "Onion": 5, "Tobacco": 6, "Wheat": 5,
    
    # Fruits
    "Apple": 6, "Banana": 8, "Guava": 6, "Mango": 6,
    "Orange": 6, "Papaya": 8, "Pomegranate": 6,
    
    # Fibre & spice
    "Cotton": 6, "Soanf": 4,
}


if __name__ == "__main__":
    # Show district loading status first
    print(f"District coordinates loaded: {len(DISTRICT_COORDS)} districts")
    if DISTRICT_COORDS:
        print("\nSample districts:")
        for i, (district, coords) in enumerate(list(DISTRICT_COORDS.items())[:5]):
            print(f"  {district}: {coords}")
    
    # Validate configuration
    try:
        Config.validate()
        print("\n✓ Configuration valid")
        print(f"  Model directory: {Config.MODEL_DIR}")
        print(f"  API host: {Config.API_HOST}:{Config.API_PORT}")
        print(f"  Supported crops: {len(CROP_HORIZONS)}")
        print(f"  Supported districts: {len(DISTRICT_COORDS)}")
        
        # Test district normalization
        print("\n✓ Testing district name normalization:")
        test_cases = [
            "Ahmedabad", "ahmedabad", "Ahmadabad",
            "Vadodara", "Vadodara (Baroda)",
            "The Dangs", "thedangs",
            "Gir Somnath", "girsomnath"
        ]
        
        for test in test_cases:
            normalized = normalize_district_name(test)
            in_coords = "✓" if normalized in DISTRICT_COORDS else "✗"
            print(f"  {in_coords} '{test}' → '{normalized}'")
            
    except RuntimeError as e:
        print(f"\n✗ Configuration validation failed:\n{e}")
        print("\nNote: Set DATA_GOV_API_KEY in .env file to resolve this.")
