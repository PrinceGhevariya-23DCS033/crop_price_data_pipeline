"""
Monthly Data Cache Manager
Gujarat Crop Price Forecasting System

Manages cached monthly data for:
- Latest mandi prices (by commodity-district)
- Rainfall data (by district)
- NDVI data (by district)

Cache is updated monthly after NDVI becomes available (16-20th of each month).
This significantly speeds up predictions by avoiding real-time API calls.
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path

try:
    from config import normalize_district_name
except ImportError:
    from src.config import normalize_district_name


class MonthlyDataCache:
    """
    Manages monthly cached data for fast predictions.
    
    Cache Structure:
    monthly_cache/
        current_month.json          # Metadata about current cache
        prices/
            {commodity}_{district}.json
        rainfall/
            {district}.json
        ndvi/
            {district}.json
    """
    
    def __init__(self, cache_dir: str = "monthly_cache"):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cached data
        """
        self.cache_dir = Path(cache_dir)
        self.prices_dir = self.cache_dir / "prices"
        self.rainfall_dir = self.cache_dir / "rainfall"
        self.ndvi_dir = self.cache_dir / "ndvi"
        
        # Create directories if they don't exist
        self.cache_dir.mkdir(exist_ok=True)
        self.prices_dir.mkdir(exist_ok=True)
        self.rainfall_dir.mkdir(exist_ok=True)
        self.ndvi_dir.mkdir(exist_ok=True)
        
        self.metadata_file = self.cache_dir / "cache_metadata.json"
    
    
    # ============ METADATA MANAGEMENT ============
    
    def get_cache_metadata(self) -> Dict:
        """Get cache metadata (last update time, version, etc.)"""
        if not self.metadata_file.exists():
            return {
                "last_updated": None,
                "update_year": None,
                "update_month": None,
                "version": "1.0",
                "commodities_cached": [],
                "districts_cached": []
            }
        
        with open(self.metadata_file, 'r') as f:
            return json.load(f)
    
    
    def update_metadata(
        self,
        year: int,
        month: int,
        commodities: List[str],
        districts: List[str]
    ):
        """Update cache metadata after refresh."""
        metadata = {
            "last_updated": datetime.now().isoformat(),
            "update_year": year,
            "update_month": month,
            "version": "1.0",
            "commodities_cached": sorted(list(set(commodities))),
            "districts_cached": sorted(list(set(districts)))
        }
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    
    def is_cache_current(self) -> bool:
        """
        Check if cache is current for this month.
        Cache should be updated after 20th of each month.
        """
        metadata = self.get_cache_metadata()
        
        if not metadata["last_updated"]:
            return False
        
        now = datetime.now()
        
        # Cache is current if it's for current month and we're before 20th,
        # OR if it's for current month and we're after 20th
        if metadata["update_year"] == now.year and metadata["update_month"] == now.month:
            return True
        
        # If we're past 20th and cache is from previous month, it's outdated
        if now.day >= 20:
            return False
        
        return True
    
    
    # ============ PRICE CACHE ============
    
    def save_price(
        self,
        commodity: str,
        district: str,
        year: int,
        month: int,
        price_data: Dict
    ):
        """
        Save latest price for commodity-district.
        
        Args:
            commodity: Crop name
            district: District name
            year: Year
            month: Month
            price_data: Dict with monthly_mean_price, days_traded, etc.
        """
        filename = f"{commodity.lower().replace(' ', '_')}_{district.lower().replace(' ', '_')}.json"
        filepath = self.prices_dir / filename
        
        data = {
            "commodity": commodity,
            "district": district,
            "year": year,
            "month": month,
            "cached_at": datetime.now().isoformat(),
            **price_data
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    
    def get_price(
        self,
        commodity: str,
        district: str
    ) -> Optional[Dict]:
        """Get cached price for commodity-district."""
        norm_district = normalize_district_name(district)
        filename = f"{commodity.lower().replace(' ', '_')}_{norm_district}.json"
        filepath = self.prices_dir / filename
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    
    # ============ RAINFALL CACHE ============
    
    def save_rainfall(
        self,
        district: str,
        year: int,
        month: int,
        rainfall_data: Dict
    ):
        """
        Save rainfall data for district-month.
        
        Args:
            district: District name
            year: Year
            month: Month
            rainfall_data: Dict with monthly_rain_sum, monthly_rain_mean
        """
        filename = f"{district.lower().replace(' ', '_')}.json"
        filepath = self.rainfall_dir / filename
        
        data = {
            "district": district,
            "year": year,
            "month": month,
            "cached_at": datetime.now().isoformat(),
            **rainfall_data
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    
    def get_rainfall(
        self,
        district: str
    ) -> Optional[Dict]:
        """Get cached rainfall for district."""
        norm_district = normalize_district_name(district)
        filename = f"{norm_district}.json"
        filepath = self.rainfall_dir / filename
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    
    # ============ NDVI CACHE ============
    
    def save_ndvi(
        self,
        district: str,
        year: int,
        month: int,
        ndvi_data: Dict
    ):
        """
        Save NDVI data for district-month.
        
        Args:
            district: District name
            year: Year
            month: Month (previous month, since NDVI lags)
            ndvi_data: Dict with monthly_ndvi_mean
        """
        filename = f"{district.lower().replace(' ', '_')}.json"
        filepath = self.ndvi_dir / filename
        
        data = {
            "district": district,
            "year": year,
            "month": month,
            "cached_at": datetime.now().isoformat(),
            **ndvi_data
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    
    def get_ndvi(
        self,
        district: str
    ) -> Optional[Dict]:
        """Get cached NDVI for district."""
        norm_district = normalize_district_name(district)
        filename = f"{norm_district}.json"
        filepath = self.ndvi_dir / filename
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    
    # ============ BULK OPERATIONS ============
    
    def get_all_cached_commodities(self) -> List[str]:
        """Get list of all commodities with cached data."""
        metadata = self.get_cache_metadata()
        return metadata.get("commodities_cached", [])
    
    
    def get_all_cached_districts(self) -> List[str]:
        """Get list of all districts with cached data."""
        metadata = self.get_cache_metadata()
        return metadata.get("districts_cached", [])
    
    
    def clear_cache(self):
        """Clear all cached data."""
        import shutil
        
        for directory in [self.prices_dir, self.rainfall_dir, self.ndvi_dir]:
            shutil.rmtree(directory, ignore_errors=True)
            directory.mkdir(exist_ok=True)
        
        if self.metadata_file.exists():
            self.metadata_file.unlink()
    
    
    def get_cache_stats(self) -> Dict:
        """Get statistics about cached data."""
        metadata = self.get_cache_metadata()
        
        price_files = len(list(self.prices_dir.glob("*.json")))
        rainfall_files = len(list(self.rainfall_dir.glob("*.json")))
        ndvi_files = len(list(self.ndvi_dir.glob("*.json")))
        
        return {
            "last_updated": metadata.get("last_updated"),
            "update_year": metadata.get("update_year"),
            "update_month": metadata.get("update_month"),
            "is_current": self.is_cache_current(),
            "total_price_entries": price_files,
            "total_rainfall_entries": rainfall_files,
            "total_ndvi_entries": ndvi_files,
            "commodities_count": len(metadata.get("commodities_cached", [])),
            "districts_count": len(metadata.get("districts_cached", []))
        }
