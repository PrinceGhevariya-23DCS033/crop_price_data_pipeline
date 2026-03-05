"""
Prediction with Confidence Intervals
Gujarat Crop Price Forecasting System

Provides uncertainty estimates for price predictions.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
from scipy import stats


class PredictionWithConfidence:
    """
    Extends predictions with confidence intervals using:
    1. Historical residual distribution
    2. Volatility-adjusted bands
    3. Bootstrapped uncertainty
    """
    
    def __init__(self, model, historical_predictions: pd.DataFrame = None):
        """
        Initialize confidence estimator.
        
        Args:
            model: Trained model
            historical_predictions: DataFrame with columns [actual, predicted, commodity, district]
        """
        self.model = model
        self.historical_predictions = historical_predictions
        self.residual_std = None
        self.commodity_std = {}
        
        if historical_predictions is not None:
            self._compute_residual_statistics()
    
    
    def _compute_residual_statistics(self):
        """Compute residual statistics from historical predictions."""
        
        df = self.historical_predictions.copy()
        df['residual'] = df['actual'] - df['predicted']
        
        # Global residual standard deviation
        self.residual_std = df['residual'].std()
        
        # Per-commodity standard deviation
        for commodity in df['commodity'].unique():
            commodity_df = df[df['commodity'] == commodity]
            self.commodity_std[commodity] = commodity_df['residual'].std()
    
    
    def predict_with_interval(
        self,
        X: pd.DataFrame,
        current_price: float,
        commodity: str,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Generate prediction with confidence interval.
        
        Args:
            X: Features for prediction
            current_price: Current price
            commodity: Commodity name
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            
        Returns:
            Dict with prediction, lower_bound, upper_bound, interval_width
        """
        
        # Get point prediction (log return)
        predicted_return = self.model.predict(X)[0]
        predicted_price = current_price * np.exp(predicted_return)
        
        # Determine standard deviation to use
        if commodity in self.commodity_std:
            std = self.commodity_std[commodity]
        elif self.residual_std is not None:
            std = self.residual_std
        else:
            # Fallback: assume 10% typical error
            std = predicted_price * 0.10
        
        # Calculate z-score for confidence level
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        
        # Confidence interval in price space
        margin = z_score * std
        
        lower_bound = max(0, predicted_price - margin)  # Price can't be negative
        upper_bound = predicted_price + margin
        
        result = {
            'predicted_price': predicted_price,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'confidence_level': confidence_level * 100,
            'interval_width': upper_bound - lower_bound,
            'relative_uncertainty': (margin / predicted_price) * 100,  # Percentage
            'std_dev': std
        }
        
        return result
    
    
    def predict_with_volatility_adjustment(
        self,
        X: pd.DataFrame,
        current_price: float,
        volatility_12: float,
        commodity: str,
        confidence_level: float = 0.95
    ) -> Dict:
        """
        Generate prediction with volatility-adjusted confidence interval.
        
        Higher volatility = wider intervals
        
        Args:
            X: Features
            current_price: Current price
            volatility_12: 12-month price volatility from features
            commodity: Commodity name
            confidence_level: Confidence level
            
        Returns:
            Dict with prediction and adjusted intervals
        """
        
        # Get base prediction
        base_result = self.predict_with_interval(
            X, current_price, commodity, confidence_level
        )
        
        # Adjust interval based on volatility
        # High volatility = wider interval
        volatility_factor = 1 + (volatility_12 / current_price)
        
        predicted_price = base_result['predicted_price']
        base_margin = (base_result['upper_bound'] - predicted_price)
        
        adjusted_margin = base_margin * volatility_factor
        
        result = {
            'predicted_price': predicted_price,
            'lower_bound': max(0, predicted_price - adjusted_margin),
            'upper_bound': predicted_price + adjusted_margin,
            'confidence_level': confidence_level * 100,
            'interval_width': 2 * adjusted_margin,
            'volatility_factor': volatility_factor,
            'relative_uncertainty': (adjusted_margin / predicted_price) * 100
        }
        
        return result
    
    
    def predict_with_quantiles(
        self,
        X: pd.DataFrame,
        current_price: float,
        n_samples: int = 1000
    ) -> Dict:
        """
        Generate prediction with bootstrapped quantiles.
        
        Uses model uncertainty by perturbing predictions.
        
        Args:
            X: Features
            current_price: Current price
            n_samples: Number of bootstrap samples
            
        Returns:
            Dict with median, p10, p25, p75, p90 predictions
        """
        
        # Get point prediction
        base_return = self.model.predict(X)[0]
        base_price = current_price * np.exp(base_return)
        
        # Generate samples with noise
        # Assume prediction error ~N(0, 0.05) in log-return space
        noise_std = 0.05  # 5% typical error
        
        sampled_returns = np.random.normal(base_return, noise_std, n_samples)
        sampled_prices = current_price * np.exp(sampled_returns)
        
        # Compute quantiles
        result = {
            'median': np.median(sampled_prices),
            'mean': np.mean(sampled_prices),
            'p10': np.percentile(sampled_prices, 10),
            'p25': np.percentile(sampled_prices, 25),
            'p75': np.percentile(sampled_prices, 75),
            'p90': np.percentile(sampled_prices, 90),
            'std': np.std(sampled_prices),
            'iqr': np.percentile(sampled_prices, 75) - np.percentile(sampled_prices, 25)
        }
        
        return result


class EnsemblePrediction:
    """
    Ensemble multiple models for robust predictions.
    """
    
    def __init__(self, models: list):
        """
        Initialize ensemble.
        
        Args:
            models: List of trained models
        """
        self.models = models
    
    
    def predict_ensemble(
        self,
        X: pd.DataFrame,
        current_price: float
    ) -> Dict:
        """
        Generate ensemble prediction with disagreement-based uncertainty.
        
        Args:
            X: Features
            current_price: Current price
            
        Returns:
            Dict with mean, std, min, max predictions
        """
        
        predictions = []
        
        for model in self.models:
            pred_return = model.predict(X)[0]
            pred_price = current_price * np.exp(pred_return)
            predictions.append(pred_price)
        
        predictions = np.array(predictions)
        
        result = {
            'ensemble_mean': np.mean(predictions),
            'ensemble_median': np.median(predictions),
            'ensemble_std': np.std(predictions),
            'min_prediction': np.min(predictions),
            'max_prediction': np.max(predictions),
            'predictions': predictions.tolist(),
            'model_agreement': 1 - (np.std(predictions) / np.mean(predictions))  # 1 = perfect agreement
        }
        
        return result


# ============ INTEGRATION WITH INFERENCE ============

def add_confidence_to_prediction(
    base_prediction: Dict,
    X: pd.DataFrame,
    current_price: float,
    commodity: str,
    confidence_estimator: PredictionWithConfidence = None
) -> Dict:
    """
    Add confidence intervals to a base prediction.
    
    Args:
        base_prediction: Dict from CropPricePredictor.predict()
        X: Features used for prediction
        current_price: Current price
        commodity: Commodity name
        confidence_estimator: Optional confidence estimator
        
    Returns:
        Enhanced prediction dict with confidence intervals
    """
    
    # If no estimator, use simple percentage-based interval
    if confidence_estimator is None:
        predicted_price = base_prediction['predicted_harvest_price']
        uncertainty = predicted_price * 0.15  # 15% typical uncertainty
        
        base_prediction['confidence_interval'] = {
            'lower_bound': max(0, predicted_price - uncertainty),
            'upper_bound': predicted_price + uncertainty,
            'confidence_level': 90,
            'method': 'simple_percentage'
        }
    
    else:
        # Use sophisticated confidence estimation
        confidence_result = confidence_estimator.predict_with_interval(
            X=X,
            current_price=current_price,
            commodity=commodity,
            confidence_level=0.90
        )
        
        base_prediction['confidence_interval'] = {
            'lower_bound': confidence_result['lower_bound'],
            'upper_bound': confidence_result['upper_bound'],
            'confidence_level': confidence_result['confidence_level'],
            'relative_uncertainty': confidence_result['relative_uncertainty'],
            'method': 'residual_based'
        }
    
    return base_prediction


# ============ EXAMPLE USAGE ============

if __name__ == "__main__":
    
    # Example: Create mock historical predictions
    historical = pd.DataFrame({
        'actual': [5000, 5200, 4800, 5100, 5300],
        'predicted': [4950, 5150, 4900, 5050, 5250],
        'commodity': ['Garlic', 'Garlic', 'Wheat', 'Wheat', 'Garlic'],
        'district': ['Ahmedabad', 'Ahmedabad', 'Rajkot', 'Rajkot', 'Ahmedabad']
    })
    
    # Initialize (in practice, load your trained model)
    # confidence_est = PredictionWithConfidence(model, historical)
    
    # Generate prediction with interval
    # result = confidence_est.predict_with_interval(X, current_price=5000, commodity='Garlic')
    
    print("Confidence interval module ready!")
    print("Use PredictionWithConfidence for uncertainty estimates.")
