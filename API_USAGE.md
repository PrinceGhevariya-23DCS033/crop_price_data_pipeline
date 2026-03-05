# API Usage Examples

## Quick Start Examples

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "model": "loaded",
  "data_fetcher": "loaded",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

### 2. Get All Supported Crops

```bash
curl http://localhost:8000/crops
```

**Response:**
```json
[
  "Ajwan",
  "Amaranthus",
  "Apple",
  "Banana",
  "Beans",
  ...
]
```

---

### 3. Get Crop Growth Horizon

```bash
curl http://localhost:8000/crops/Garlic/horizon
```

**Response:**
```json
{
  "commodity": "Garlic",
  "growth_horizon_months": 6,
  "description": "Garlic takes approximately 6 months from sowing to harvest"
}
```

---

### 4. Make a Prediction (Manual Data)

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "commodity": "Garlic",
    "district": "Ahmedabad",
    "current_price": 5000,
    "year": 2024,
    "month": 1,
    "monthly_rain_sum": 50,
    "monthly_rain_mean": 2.5,
    "monthly_ndvi_mean": 0.6,
    "days_traded": 20
  }'
```

**Response:**
```json
{
  "commodity": "Garlic",
  "district": "Ahmedabad",
  "current_month": "2024-01",
  "current_price": 5000.0,
  "growth_horizon_months": 6,
  "harvest_window_start": "2024-07",
  "predicted_harvest_price": 5250.75,
  "expected_return_percent": 4.98,
  "absolute_change": 250.75,
  "model_type": "LightGBM",
  "prediction_timestamp": "2024-01-15T10:45:00.000Z",
  "confidence_interval": {
    "lower_bound": 4463.14,
    "upper_bound": 6038.36,
    "confidence_level": 90,
    "uncertainty_percent": 15.0
  }
}
```

---

### 5. Auto-Fetch Prediction

Automatically fetches current prices, weather, and NDVI:

```bash
curl -X POST "http://localhost:8000/predict/auto?commodity=Wheat&district=Rajkot&year=2024&month=1"
```

**Response:**
```json
{
  "commodity": "Wheat",
  "district": "Rajkot",
  "current_month": "2024-01",
  "current_price": 2250.50,
  "growth_horizon_months": 5,
  "harvest_window_start": "2024-06",
  "predicted_harvest_price": 2380.25,
  "expected_return_percent": 5.76,
  "absolute_change": 129.75,
  "fetched_data": {
    "current_price": 2250.50,
    "rain_sum": 45.2,
    "ndvi": 0.58,
    "days_traded": 22
  },
  "confidence_interval": {
    "lower_bound": 2023.21,
    "upper_bound": 2737.29,
    "confidence_level": 90,
    "uncertainty_percent": 15.0
  }
}
```

---

### 6. Compare Multiple Crops

```bash
curl -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d '{
    "district": "Ahmedabad",
    "commodities": ["Garlic", "Wheat", "Cotton", "Onion"],
    "year": 2024,
    "month": 1
  }'
```

**Response:**
```json
{
  "district": "Ahmedabad",
  "comparison_month": "2024-01",
  "crops_compared": 4,
  "recommendations": [
    {
      "commodity": "Cotton",
      "current_price": 6500.0,
      "predicted_harvest_price": 7150.25,
      "expected_return_percent": 10.0,
      "growth_horizon_months": 6,
      "harvest_window_start": "2024-07"
    },
    {
      "commodity": "Garlic",
      "current_price": 5000.0,
      "predicted_harvest_price": 5250.75,
      "expected_return_percent": 5.0,
      "growth_horizon_months": 6,
      "harvest_window_start": "2024-07"
    },
    {
      "commodity": "Wheat",
      "current_price": 2200.0,
      "predicted_harvest_price": 2288.0,
      "expected_return_percent": 4.0,
      "growth_horizon_months": 5,
      "harvest_window_start": "2024-06"
    },
    {
      "commodity": "Onion",
      "current_price": 2500.0,
      "predicted_harvest_price": 2525.0,
      "expected_return_percent": 1.0,
      "growth_horizon_months": 5,
      "harvest_window_start": "2024-06"
    }
  ]
}
```

---

### 7. Get Historical Prices

```bash
curl "http://localhost:8000/historical/Garlic/Ahmedabad?months=12"
```

**Response:**
```json
{
  "commodity": "Garlic",
  "district": "Ahmedabad",
  "months_returned": 12,
  "data": [
    {
      "date": "2023-02-01",
      "monthly_mean_price": 4800.5,
      "days_traded": 20
    },
    {
      "date": "2023-03-01",
      "monthly_mean_price": 5000.25,
      "days_traded": 22
    },
    ...
  ]
}
```

---

### 8. Get Available Districts

```bash
curl http://localhost:8000/districts
```

**Response:**
```json
{
  "count": 33,
  "districts": [
    "Ahmadabad",
    "Amreli",
    "Anand",
    "Aravalli",
    "BanasKantha",
    ...
  ],
  "note": "District names are normalized. Variations like 'Ahmedabad' will be mapped to 'Ahmadabad'"
}
```

**District Name Variations:**

The API automatically normalizes district names. You can use any of these variations:
- "Ahmedabad", "ahmedabad" → "Ahmadabad"
- "Vadodara", "Vadodara (Baroda)" → "Vadodara"
- "The Dangs", "thedangs" → "TheDangs"
- "Gir Somnath", "girsomnath" → "GirSomnath"
- "Devbhumi Dwarka", "devbhumidwarka" → "DevbhumiDwarka"
- "Chhota Udaipur", "chhotaudaipur" → "ChhotaUdaipur"
- "Mehsana", "mehsana" → "Mahesana"
- And more...

---

## Python Client Example

```python
import requests

API_BASE = "http://localhost:8000"

# Get all crops
response = requests.get(f"{API_BASE}/crops")
crops = response.json()
print(f"Available crops: {len(crops)}")

# Make prediction
prediction_data = {
    "commodity": "Garlic",
    "district": "Ahmedabad",
    "current_price": 5000,
    "year": 2024,
    "month": 1,
    "monthly_rain_sum": 50,
    "monthly_rain_mean": 2.5,
    "monthly_ndvi_mean": 0.6,
    "days_traded": 20
}

response = requests.post(
    f"{API_BASE}/predict",
    json=prediction_data
)

prediction = response.json()
print(f"Predicted price: ₹{prediction['predicted_harvest_price']:.2f}")
print(f"Expected return: {prediction['expected_return_percent']:.2f}%")
print(f"Confidence interval: ₹{prediction['confidence_interval']['lower_bound']:.2f} - ₹{prediction['confidence_interval']['upper_bound']:.2f}")
```

---

## JavaScript/Frontend Example

```javascript
// Make prediction
async function predictPrice() {
    const response = await fetch('http://localhost:8000/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            commodity: 'Garlic',
            district: 'Ahmedabad',
            current_price: 5000,
            year: 2024,
            month: 1,
            monthly_rain_sum: 50,
            monthly_rain_mean: 2.5,
            monthly_ndvi_mean: 0.6,
            days_traded: 20
        })
    });
    
    const prediction = await response.json();
    
    console.log(`Predicted price: ₹${prediction.predicted_harvest_price}`);
    console.log(`Expected return: ${prediction.expected_return_percent}%`);
}

// Compare crops
async function compareCrops() {
    const response = await fetch('http://localhost:8000/compare', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            district: 'Ahmedabad',
            commodities: ['Garlic', 'Wheat', 'Cotton'],
            year: 2024,
            month: 1
        })
    });
    
    const comparison = await response.json();
    
    console.log('Top crop:', comparison.recommendations[0].commodity);
    console.log('Best return:', comparison.recommendations[0].expected_return_percent + '%');
}
```

---

## Error Handling

### 404 - Commodity Not Found

```json
{
  "detail": "Crop 'InvalidCrop' not found. Use /crops to see supported crops."
}
```

### 404 - No Historical Data

```json
{
  "detail": "Historical data not found for Garlic"
}
```

### 400 - Missing Features

```json
{
  "detail": "Missing feature values: ['price_lag_12']. Need at least 12 months of history."
}
```

### 503 - Service Unavailable

```json
{
  "detail": "Model not available"
}
```

---

## Rate Limiting Recommendations

For production deployment, consider:
- Rate limiting: 100 requests/minute per IP
- Caching predictions for same parameters (5 minutes)
- Batch prediction endpoints for multiple queries

---

## Testing the API

### Using httpie

```bash
# Install httpie
pip install httpie

# Get crops
http GET localhost:8000/crops

# Make prediction
http POST localhost:8000/predict \
    commodity="Garlic" \
    district="Ahmedabad" \
    current_price:=5000 \
    year:=2024 \
    month:=1 \
    monthly_rain_sum:=50 \
    monthly_rain_mean:=2.5 \
    monthly_ndvi_mean:=0.6 \
    days_traded:=20
```

### Using Postman

1. Import the API: `http://localhost:8000/openapi.json`
2. Test endpoints interactively
3. Generate client code in multiple languages

---

For more details, visit the interactive API documentation at:
**http://localhost:8000/docs**
