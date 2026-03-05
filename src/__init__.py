"""
Gujarat Crop Price Forecasting System
Source Package Initialization
"""

__version__ = "1.0.0"
__author__ = "Gujarat Crop Price Team"
__description__ = "Pre-production harvest-window crop price forecasting for Gujarat"

# Import main classes for easier access
from .inference import CropPricePredictor
from .data_fetchers import (
    MandiPriceFetcher,
    WeatherFetcher,
    NDVIFetcher,
    CombinedDataFetcher
)
from .confidence import PredictionWithConfidence
from .config import Config, DISTRICT_COORDS, normalize_district_name

__all__ = [
    "CropPricePredictor",
    "MandiPriceFetcher",
    "WeatherFetcher",
    "NDVIFetcher",
    "CombinedDataFetcher",
    "PredictionWithConfidence",
    "Config",
    "DISTRICT_COORDS",
    "normalize_district_name"
]
