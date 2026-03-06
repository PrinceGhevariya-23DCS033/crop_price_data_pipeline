"""
Data Fetching Utilities
Gujarat Crop Price Forecasting System

Fetches real-time data from:
1. data.gov.in - Mandi prices
2. Open-Meteo - Weather data
3. Google Earth Engine - NDVI
"""

import os
import time
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from requests.exceptions import RequestException, Timeout

# Import configuration
from config import DISTRICT_COORDS, normalize_district_name, agmarknet_district_name


# ============ MANDI PRICE FETCHER ============

class MandiPriceFetcher:
    """
    Fetch crop prices from data.gov.in Agmarknet API.
    """
    
    def __init__(self, api_key: Optional[str] = None, use_api: bool = True):
        """
        Initialize fetcher.
        
        Args:
            api_key: data.gov.in API key (or reads from env DATA_GOV_API_KEY)
            use_api: Whether to use API (default: True for fresh data)
        """
        self.api_key = api_key or os.getenv("DATA_GOV_API_KEY")
        self.use_api = use_api and bool(self.api_key)
        
        self.resource_id = "35985678-0d79-46b4-9ed6-6f13308a1d24"
        self.base_url = f"https://api.data.gov.in/resource/{self.resource_id}"
        self.timeout = 30
        # Retry strategy: attempts per round and backoff between rounds (seconds)
        self.attempts_per_round = 5
        # First backoff: 2 minutes, second backoff: 5 minutes
        self.retry_backoffs = [120, 300]
        
        if not self.use_api:
            print("ℹ️  API disabled - will use CSV fallback")
        else:
            print("✓ API enabled - will fetch latest data from data.gov.in")
    
    
    def fetch_latest_prices(
        self,
        state: str = "Gujarat",
        commodity: Optional[str] = None,
        district: Optional[str] = None,
        days_back: int = 30,
        from_date: Optional[datetime] = None,
        limit: int = 10000
    ) -> pd.DataFrame:
        """
        Fetch ONLY recent mandi prices (optimized for latest data).
        
        Args:
            state: State name (default: Gujarat)
            commodity: Specific commodity (optional)
            district: Specific district (optional)
            days_back: Number of days to look back (default: 30)
            limit: Max records to fetch (default: 10000 for better coverage)
            
        Returns:
            DataFrame with recent records only, sorted by date descending
        """
        
        if not self.api_key:
            return pd.DataFrame()
        
        params = {
            "api-key": self.api_key,
            "format": "json",
            "limit": limit,
            "offset": 0,
            "filters[State]": state
        }
        
        if commodity:
            params["filters[Commodity]"] = commodity

        if district:
            # Use exact Agmarknet API name (case-sensitive on data.gov.in)
            params["filters[District]"] = agmarknet_district_name(district)
        
        # Calculate cutoff date
        if from_date is not None:
            cutoff_date = from_date
        else:
            cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Multi-round retry with backoff:
        #   Round 1: 5 attempts (5 s apart)
        #   → sleep 2 min →
        #   Round 2: 5 attempts (5 s apart)
        #   → sleep 5 min →
        #   Round 3: 5 final attempts (5 s apart) then give up
        def _get_with_retries(url, params):
            rounds = len(self.retry_backoffs) + 1          # 3 rounds total
            INTER_ATTEMPT_SLEEP = 5                        # seconds between attempts within a round

            for r in range(rounds):
                for attempt in range(self.attempts_per_round):
                    try:
                        response = requests.get(url, params=params, timeout=self.timeout)

                        if response.status_code == 200:
                            return response

                        # Non-200: short wait then retry
                        if attempt < self.attempts_per_round - 1:
                            time.sleep(INTER_ATTEMPT_SLEEP)

                    except (Timeout, RequestException):
                        if attempt < self.attempts_per_round - 1:
                            time.sleep(INTER_ATTEMPT_SLEEP)

                # All attempts in this round failed — sleep before next round
                if r < len(self.retry_backoffs):
                    backoff = self.retry_backoffs[r]
                    mins = backoff // 60
                    print(f"    ⚠ Round {r+1} failed ({self.attempts_per_round} attempts) — sleeping {mins} min before round {r+2}...")
                    time.sleep(backoff)

            return None

        response = _get_with_retries(self.base_url, params)
        if response is None:
            return pd.DataFrame()

        try:
            data = response.json()
        except Exception:
            return pd.DataFrame()

        records = data.get("records", [])

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)

        # Parse dates and prices
        df["Arrival_Date"] = pd.to_datetime(df["Arrival_Date"], dayfirst=True, errors="coerce")
        df["Modal_Price"] = pd.to_numeric(df["Modal_Price"], errors="coerce")

        # Remove invalid rows
        df = df.dropna(subset=["Commodity", "Arrival_Date", "Modal_Price"])

        if df.empty:
            return pd.DataFrame()

        # FILTER: Keep only recent data
        df = df[df["Arrival_Date"] >= cutoff_date]

        # Sort by date descending (newest first)
        df = df.sort_values("Arrival_Date", ascending=False)

        return df
    
    
    def compute_monthly_average(
        self,
        commodity: str,
        district: str,
        year: int,
        month: int
    ) -> Optional[Dict]:
        """
        Compute monthly average price for a commodity-district-month.
        
        Args:
            commodity: Crop name
            district: District name
            year: Year
            month: Month (1-12)
            
        Returns:
            Dict with monthly_mean_price and days_traded
        """
        
        # Fetch all records for the commodity-district
        df = self.fetch_latest_prices(
            state="Gujarat",
            commodity=commodity,
            district=district,
            limit=5000
        )
        
        if df.empty:
            return None
        
        # Filter for specific month
        df["year"] = df["Arrival_Date"].dt.year
        df["month"] = df["Arrival_Date"].dt.month
        
        monthly_data = df[
            (df["year"] == year) & 
            (df["month"] == month)
        ]
        
        if monthly_data.empty:
            return None
        
        result = {
            "commodity": commodity,
            "district": district,
            "year": year,
            "month": month,
            "monthly_mean_price": monthly_data["Modal_Price"].mean(),
            "days_traded": monthly_data["Arrival_Date"].nunique(),
            "min_price": monthly_data["Modal_Price"].min(),
            "max_price": monthly_data["Modal_Price"].max(),
            "std_price": monthly_data["Modal_Price"].std()
        }
        
        return result
    
    
    def fetch_historical_monthly_prices(
        self,
        commodity: str,
        district: str,
        months_back: int = 18
    ) -> pd.DataFrame:
        """
        Fetch last N months of historical data from CSV files (API data is outdated).
        
        Args:
            commodity: Crop name
            district: District name  
            months_back: Number of past months to fetch
            
        Returns:
            DataFrame with monthly aggregated data
        """
        
        # Map commodity to filename
        commodity_file = commodity.lower().replace(" ", "_") + "_final.csv"
        file_path = os.path.join("processed", commodity_file)
        
        if not os.path.exists(file_path):
            print(f"  ⚠ CSV file not found: {file_path}")
            return pd.DataFrame()
        
        # Load CSV data
        df = pd.read_csv(file_path)
        
        # Ensure date column exists
        if "date" not in df.columns:
            return pd.DataFrame()
        
        df["date"] = pd.to_datetime(df["date"])
        
        # Normalize district name for filtering
        from config import normalize_district_name
        normalized_district = normalize_district_name(district)
        
        # Filter for district (try normalized name)
        if "district" in df.columns:
            df["district_norm"] = df["district"].apply(normalize_district_name)
            df = df[df["district_norm"] == normalized_district].copy()
        
        if df.empty:
            print(f"  ⚠ No data for {commodity} in {district}")
            return pd.DataFrame()
        
        # Sort by date and get last N months
        df = df.sort_values("date").tail(months_back)
        
        # **FIX: Normalize district names to match prediction input**
        df["district"] = normalized_district
        
        # Ensure required columns exist
        if "commodity" not in df.columns:
            df["commodity"] = commodity
        if "year" not in df.columns:
            df["year"] = df["date"].dt.year
        if "month" not in df.columns:
            df["month"] = df["date"].dt.month
        
        return df
    
    
    def get_current_price_with_fallback(
        self,
        commodity: str,
        district: str,
        reference_date: Optional[datetime] = None,
        days_15: int = 15,
        days_30: int = 30,
        last_cached_data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Get current price with smart fallback logic FOR CACHE JSON FORMAT.

        Search strategy:
          • No existing cache  → search API from 2026-01-01; if nothing → CSV fallback.
          • Existing cache     → search API from last_date in cached JSON;
                                 if nothing → reuse cached JSON (no CSV).

        Returns:
            Dict in cache format: {commodity, district, year, month, cached_at,
                                  monthly_mean_price, days_traded, data_source, last_date}
        """
        if reference_date is None:
            reference_date = datetime.now()

        # ── Determine API search start date ────────────────────────────────
        ANCHOR_DATE = datetime(2026, 1, 1)  # Earliest date to search on first run

        if last_cached_data and last_cached_data.get("last_date"):
            search_from = datetime.strptime(last_cached_data["last_date"], "%Y-%m-%d")
            use_cache_fallback = True
            print(f"  (resuming from last cached date: {search_from.strftime('%Y-%m-%d')})")
        else:
            search_from = ANCHOR_DATE
            use_cache_fallback = False
            print(f"  (first run: searching back to {ANCHOR_DATE.strftime('%Y-%m-%d')})")

        # ── STEP 1: Try API ─────────────────────────────────────────────────
        if self.use_api:
            print(f"  Fetching from API: {commodity} - {district}")
            try:
                api_df = self.fetch_latest_prices(
                    state="Gujarat",
                    commodity=commodity,
                    district=district,
                    from_date=search_from,
                    limit=10000
                )

                if not api_df.empty:
                    latest_date = api_df["Arrival_Date"].max()
                    oldest_date = api_df["Arrival_Date"].min()
                    print(f"    ✓ API: {len(api_df)} records from {oldest_date.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')}")
                    return {
                        "commodity": commodity,
                        "district": district,
                        "year": reference_date.year,
                        "month": reference_date.month,
                        "cached_at": datetime.now().isoformat(),
                        "monthly_mean_price": float(api_df["Modal_Price"].mean()),
                        "days_traded": int(api_df["Arrival_Date"].nunique()),
                        "data_source": "API",
                        "last_date": latest_date.strftime("%Y-%m-%d"),
                        "price_source": "API"
                    }
                else:
                    print(f"    ⚠ API returned no data since {search_from.strftime('%Y-%m-%d')}")

            except Exception as e:
                print(f"    ⚠ API fetch error: {e}")

        # ── STEP 2: Fallback ────────────────────────────────────────────────
        if use_cache_fallback and last_cached_data and last_cached_data.get("monthly_mean_price"):
            # Subsequent run — no new API data → reuse last cached price as-is
            print(f"  ↩ No new API data — reusing last cached price (last_date: {last_cached_data.get('last_date', 'N/A')})")
            result = dict(last_cached_data)
            result["price_source"] = f"CACHE_REUSE (no new data since {last_cached_data.get('last_date', 'N/A')})"
            result["data_source"] = "CACHE_REUSE"
            result["cached_at"] = datetime.now().isoformat()
            return result

        # ── STEP 3: CSV fallback (first run only) ───────────────────────────
        print(f"  Falling back to CSV data...")

        commodity_file = commodity.lower().replace(" ", "_") + "_final.csv"
        file_path = os.path.join("processed", commodity_file)

        if not os.path.exists(file_path):
            print(f"    ❌ CSV file not found: {file_path}")
            return None

        df = pd.read_csv(file_path)

        if "date" not in df.columns or "monthly_mean_price" not in df.columns:
            print(f"    ❌ CSV missing required columns")
            return None

        df["date"] = pd.to_datetime(df["date"])

        # Filter for district
        from config import normalize_district_name
        normalized_district = normalize_district_name(district)

        if "district" in df.columns:
            df["district_norm"] = df["district"].apply(normalize_district_name)
            df = df[df["district_norm"] == normalized_district].copy()

        if df.empty:
            print(f"    ❌ No CSV data for district: {district}")
            return None

        # Use the most recent rows available
        df = df.sort_values("date", ascending=False)
        df_recent = df.head(days_30)
        latest_date = df_recent["date"].max()

        print(f"    ✓ CSV: {len(df_recent)} records, latest: {latest_date.strftime('%Y-%m-%d')}")

        return {
            "commodity": commodity,
            "district": district,
            "year": reference_date.year,
            "month": reference_date.month,
            "cached_at": datetime.now().isoformat(),
            "monthly_mean_price": float(df_recent["monthly_mean_price"].mean()),
            "days_traded": int(len(df_recent)),
            "data_source": "CSV",
            "last_date": latest_date.strftime("%Y-%m-%d"),
            "price_source": "CSV"
        }


# ============ WEATHER DATA FETCHER ============

class WeatherFetcher:
    """
    Fetch weather data from Open-Meteo API.
    Uses district coordinates from district_latlon.csv.
    """
    
    def __init__(self):
        """Initialize weather fetcher."""
        self.base_url = "https://archive-api.open-meteo.com/v1/archive"
        self.timeout = 30
        
        # District coordinates loaded from district_latlon.csv via config
        self.district_coords = DISTRICT_COORDS
    
    
    def get_monthly_rainfall(
        self,
        district: str,
        year: int,
        month: int
    ) -> Optional[Dict]:
        """
        Fetch monthly rainfall data for a district.
        
        Args:
            district: District name (will be normalized)
            year: Year
            month: Month (1-12)
            
        Returns:
            Dict with monthly_rain_sum and monthly_rain_mean
        """
        
        # Normalize district name
        normalized_district = normalize_district_name(district)
        
        if normalized_district not in self.district_coords:
            print(f"⚠ District '{district}' (normalized: '{normalized_district}') coordinates not found")
            return None
        
        lat, lon = self.district_coords[normalized_district]
        
        # Calculate month date range
        start_date = f"{year}-{month:02d}-01"
        
        if month == 12:
            end_date = f"{year}-{month:02d}-31"
        else:
            next_month = datetime(year, month, 1) + timedelta(days=32)
            last_day = (next_month.replace(day=1) - timedelta(days=1)).day
            end_date = f"{year}-{month:02d}-{last_day:02d}"
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "precipitation_sum",
            "timezone": "Asia/Kolkata"
        }
        
        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "daily" not in data:
                    return None
                
                daily = data["daily"]
                precipitation = daily.get("precipitation_sum", [])
                
                if not precipitation:
                    return None
                
                # Remove None values
                precip_values = [p for p in precipitation if p is not None]
                
                if not precip_values:
                    return Nonenormalized_
                
                result = {
                    "district": district,
                    "year": year,
                    "month": month,
                    "monthly_rain_sum": sum(precip_values),
                    "monthly_rain_mean": np.mean(precip_values),
                    "rain_days": sum(1 for p in precip_values if p > 0)
                }
                
                return result
            
            else:
                print(f"⚠ Open-Meteo HTTP {response.status_code}")
                return None
        
        except Exception as e:
            print(f"⚠ Weather fetch error: {e}")
            return None


# ============ NDVI FETCHER (Google Earth Engine) ============

class NDVIFetcher:
    """
    Fetch NDVI data from Google Earth Engine.
    
    Note: Requires Google Earth Engine authentication.
    For production, consider pre-computed monthly NDVI or alternative API.
    """
    
    def __init__(self):
        """Initialize NDVI fetcher."""
        self.gee_available = False
        
        try:
            import ee
            
            # Try to initialize
            try:
                ee.Initialize()
                self.gee_available = True
                self.ee = ee
                print("✓ Google Earth Engine initialized")
            except:
                print("⚠ Google Earth Engine not authenticated")
                print("  Run: earthengine authenticate")
        
        except ImportError:
            print("⚠ Google Earth Engine library not installed")
            print("  Install: pip install earthengine-api")
    
    
    def get_ndvi_from_csv(
        self,
        commodity: str,
        district: str,
        year: int,
        month: int
    ) -> Optional[Dict]:
        """
        Get latest NDVI from CSV historical data.
        Falls back to this when GEE is not available.
        
        Args:
            commodity: Crop name
            district: District name
            year: Year 
            month: Month (1-12)
            
        Returns:
            Dict with monthly_ndvi_mean from latest available data
        """
        
        # Load commodity CSV
        commodity_file = commodity.lower().replace(" ", "_") + "_final.csv"
        file_path = os.path.join("processed", commodity_file)
        
        if not os.path.exists(file_path):
            return None
        
        df = pd.read_csv(file_path)
        
        if "date" not in df.columns or "monthly_ndvi_mean" not in df.columns:
            return None
        
        df["date"] = pd.to_datetime(df["date"])
        
        # Filter for district
        from config import normalize_district_name
        normalized_district = normalize_district_name(district)
        
        if "district" in df.columns:
            df["district_norm"] = df["district"].apply(normalize_district_name)
            df = df[df["district_norm"] == normalized_district].copy()
        
        if df.empty:
            return None
        
        # Sort by date and get latest
        df = df.sort_values("date", ascending=False)
        
        # Get NDVI value from latest available data
        latest_ndvi = df["monthly_ndvi_mean"].iloc[0]
        latest_date = df["date"].iloc[0]
        
        return {
            "district": district,
            "year": year,
            "month": month,
            "monthly_ndvi_mean": latest_ndvi,
            "source": "CSV",
            "data_date": latest_date.strftime("%Y-%m-%d")
        }
    
    
    def get_monthly_ndvi(
        self,
        district: str,
        year: int,
        month: int,
        commodity: Optional[str] = None,
        coords: Optional[Tuple[float, float]] = None
    ) -> Optional[Dict]:
        """
        Fetch monthly average NDVI for a district.
        First tries Google Earth Engine, then falls back to CSV data.
        
        Args:
            district: District name (will be normalized)
            year: Year
            month: Month (1-12)
            commodity: Crop name (for CSV fallback)
            coords: Optional (lat, lon) tuple. If None, uses district centroid.
            
        Returns:
            Dict with monthly_ndvi_mean
        """
        
        # Normalize district name
        normalized_district = normalize_district_name(district)
        
        # Try CSV first since it has actual data
        if commodity:
            csv_ndvi = self.get_ndvi_from_csv(commodity, district, year, month)
            if csv_ndvi:
                return csv_ndvi
        
        # If GEE not available, return None (caller should handle)
        if not self.gee_available:
            return None
        
        # Get coordinates
        if coords is None:
            if normalized_district not in DISTRICT_COORDS:
                return None
            lat, lon = DISTRICT_COORDS[normalized_district]
        else:
            lat, lon = coords
        
        try:
            # Define date range
            start_date = f"{year}-{month:02d}-01"
            
            if month == 12:
                end_year = year + 1
                end_month = 1
            else:
                end_year = year
                end_month = month + 1
            
            end_date = f"{end_year}-{end_month:02d}-01"
            
            # Create point geometry
            point = self.ee.Geometry.Point([lon, lat])
            
            # Load MODIS NDVI (or Sentinel-2 if preferred)
            ndvi_collection = (
                self.ee.ImageCollection("MODIS/061/MOD13Q1")
                .filterDate(start_date, end_date)
                .filterBounds(point)
                .select("NDVI")
            )
            
            # Compute mean
            ndvi_mean = ndvi_collection.mean()
            
            # Extract value at point
            ndvi_value = ndvi_mean.reduceRegion(
                reducer=self.ee.Reducer.mean(),
                geometry=point,
                scale=250
            ).getInfo()
            
            if "NDVI" in ndvi_value and ndvi_value["NDVI"] is not None:
                # MODIS NDVI is scaled by 10000
                ndvi = ndvi_value["NDVI"] / 10000.0
                
                result = {
                    "district": district,
                    "year": year,
                    "month": month,
                    "monthly_ndvi_mean": ndvi
                }
                
                return result
            
            return None
        
        except Exception as e:
            print(f"⚠ NDVI fetch error: {e}")
            return None


# ============ COMBINED DATA FETCHER ============

class CombinedDataFetcher:
    """
    Fetches all required data (prices, weather, NDVI) for prediction.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize all fetchers."""
        self.mandi_fetcher = MandiPriceFetcher(api_key)
        self.weather_fetcher = WeatherFetcher()
        self.ndvi_fetcher = NDVIFetcher()
    
    
    def fetch_prediction_data(
        self,
        commodity: str,
        district: str,
        year: int,
        month: int
    ) -> Optional[Dict]:
        """
        Fetch all required data for prediction.
        
        Args:
            commodity: Crop name
            district: District name
            year: Current year
            month: Current month
            
        Returns:
            Dict with all required fields for prediction
        """
        
        print(f"📡 Fetching data for {commodity} in {district} ({year}-{month:02d})")
        
        # Fetch mandi price
        print("  → Fetching mandi prices...")
        price_data = self.mandi_fetcher.compute_monthly_average(
            commodity, district, year, month
        )
        
        if not price_data:
            print("  ❌ No price data found")
            return None
        
        # Fetch weather
        print("  → Fetching weather data...")
        weather_data = self.weather_fetcher.get_monthly_rainfall(
            district, year, month
        )
        
        if not weather_data:
            print("  ⚠ Weather data unavailable, using defaults")
            weather_data = {
                "monthly_rain_sum": 0,
                "monthly_rain_mean": 0
            }
        
        # Fetch NDVI
        print("  → Fetching NDVI data...")
        ndvi_data = self.ndvi_fetcher.get_monthly_ndvi(
            district, year, month
        )
        
        if not ndvi_data:
            print("  ⚠ NDVI data unavailable, using default")
            ndvi_data = {"monthly_ndvi_mean": 0.5}
        
        # Combine all data
        combined = {
            **price_data,
            "monthly_rain_sum": weather_data.get("monthly_rain_sum", 0),
            "monthly_rain_mean": weather_data.get("monthly_rain_mean", 0),
            "monthly_ndvi_mean": ndvi_data.get("monthly_ndvi_mean", 0.5)
        }
        
        print("  ✓ Data fetch complete")
        
        return combined


# ============ EXAMPLE USAGE ============

if __name__ == "__main__":
    
    # Test mandi price fetcher
    print("=" * 60)
    print("Testing Mandi Price Fetcher")
    print("=" * 60)
    
    try:
        mandi = MandiPriceFetcher()
        
        # Test with Ahmadabad (using normalized name from CSV)
        result = mandi.compute_monthly_average(
            commodity="Garlic",
            district="Ahmadabad",
            year=2024,
            month=1
        )
        
        if result:
            print("\n✓ Monthly Average:")
            for key, value in result.items():
                print(f"  {key}: {value}")
    
    except Exception as e:
        print(f"⚠ Test failed: {e}")
    
    # Test weather fetcher
    print("\n" + "=" * 60)
    print("Testing Weather Fetcher")
    print("=" * 60)
    
    weather = WeatherFetcher()
    
    # Test with both variations
    for district_name in ["Ahmedabad", "Ahmadabad"]:
        print(f"\nTesting with '{district_name}':")
        weather_result = weather.get_monthly_rainfall(
            district=district_name,
            year=2024,
            month=1
        )
        
        if weather_result:
            print("✓ Monthly Rainfall:")
            for key, value in weather_result.items():
                print(f"  {key}: {value}")
    
    # Test district normalization
    print("\n" + "=" * 60)
    print("Testing District Normalization")
    print("=" * 60)
    
    test_districts = [
        "Ahmedabad", "ahmedabad", "Ahmadabad",
        "Vadodara", "Vadodara (Baroda)",
        "The Dangs", "TheDangs",
        "Gir Somnath", "GirSomnath"
    ]
    
    for district in test_districts:
        normalized = normalize_district_name(district)
        print(f"  '{district}' → '{normalized}'")
