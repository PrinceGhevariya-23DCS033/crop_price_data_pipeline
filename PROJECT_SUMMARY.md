# 🌾 Gujarat Crop Price Forecasting System - Complete Interface

## ✅ Setup Complete!

Your crop price forecasting system is now ready with a complete production interface. Here's what has been created:

---

## 📁 Project Structure

```
Crop_Price_V2/
│
├── 📊 Data & Model
│   ├── production_model/          # Trained model artifacts
│   │   ├── crop_price_model.pkl   # LightGBM model
│   │   ├── district_encoder.pkl   # District label encoder
│   │   ├── commodity_encoder.pkl  # Commodity label encoder
│   │   ├── feature_columns.pkl    # Feature column order
│   │   ├── crop_horizon.pkl       # Crop growth horizons
│   │   └── model_metadata.pkl     # Model metadata
│   │
│   ├── processed/                 # Historical processed data (CSV files)
│   ├── final/                     # Final cleaned data
│   └── Notbooks/                  # Development notebooks
│       ├── Crop_price_v2_Model_trainning_finalv2.ipynb
│       └── crop_pricev2_feture_eng.ipynb
│
├── 🔧 Backend Application
│   └── src/
│       ├── inference.py          # Core prediction engine
│       ├── data_fetchers.py      # API integrations (data.gov.in, Open-Meteo, GEE)
│       ├── confidence.py         # Confidence interval calculations
│       └── api.py                # FastAPI REST API
│
├── 🎨 Frontend Interface
│   └── frontend/
│       └── index.html            # Interactive web interface
│
├── 📚 Documentation
│   ├── README.md                 # Main documentation
│   ├── API_USAGE.md              # API endpoint examples
│   └── DEPLOYMENT.md             # Production deployment guide
│
├── 🚀 Startup Scripts
│   ├── start.bat                 # Windows startup script
│   └── start.sh                  # Linux/Mac startup script
│
├── 🧪 Testing
│   └── test_system.py            # System test suite
│
└── ⚙️ Configuration
    ├── requirements.txt          # Python dependencies
    ├── .env.example              # Environment variables template
    └── .gitignore                # Git ignore rules
```

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy environment template
copy .env.example .env    # Windows
cp .env.example .env      # Linux/Mac

# Edit .env and add your data.gov.in API key
# Get free API key: https://data.gov.in/
```

### Step 3: Run the System
```bash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh

# Or manually
cd src
python api.py
```

---

## 🌐 Access Points

After starting the system:

| Service | URL | Description |
|---------|-----|-------------|
| **API Server** | http://localhost:8000 | REST API backend |
| **Interactive Docs** | http://localhost:8000/docs | Swagger UI for API |
| **Alternative Docs** | http://localhost:8000/redoc | ReDoc API documentation |
| **Web Interface** | Open `frontend/index.html` | User-friendly web UI |

---

## 🎯 Key Features

### 1. **Inference Engine** (`src/inference.py`)
- ✅ Load trained LightGBM model
- ✅ Crop-specific growth horizons (2-8 months)
- ✅ Feature engineering pipeline
- ✅ Single & batch predictions
- ✅ Support for 45+ crops

### 2. **Data Fetchers** (`src/data_fetchers.py`)
- ✅ **Mandi prices** from data.gov.in API
- ✅ **Weather data** from Open-Meteo
- ✅ **NDVI** from Google Earth Engine (optional)
- ✅ Automatic data integration

### 3. **REST API** (`src/api.py`)
- ✅ `/crops` - List all supported crops
- ✅ `/predict` - Price prediction with manual data
- ✅ `/predict/auto` - Auto-fetch & predict
- ✅ `/compare` - Compare multiple crops
- ✅ `/historical` - Get historical prices
- ✅ `/districts` - List available districts
- ✅ CORS enabled for frontend integration

### 4. **Confidence Intervals** (`src/confidence.py`)
- ✅ Uncertainty estimation (±15% typical)
- ✅ 90% confidence intervals
- ✅ Volatility-adjusted predictions
- ✅ Quantile predictions

### 5. **Web Interface** (`frontend/index.html`)
- ✅ Single crop price prediction
- ✅ Multi-crop comparison tool
- ✅ Visual result display with confidence intervals
- ✅ Responsive design
- ✅ Real-time API integration

---

## 📊 Example API Usage

### Get Supported Crops
```bash
curl http://localhost:8000/crops
```

### Make a Prediction
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
  "current_price": 5000.0,
  "predicted_harvest_price": 5250.75,
  "expected_return_percent": 4.98,
  "growth_horizon_months": 6,
  "harvest_window_start": "2024-07",
  "confidence_interval": {
    "lower_bound": 4463.14,
    "upper_bound": 6038.36,
    "confidence_level": 90
  }
}
```

### Compare Crops
```bash
curl -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d '{
    "district": "Ahmedabad",
    "commodities": ["Garlic", "Wheat", "Cotton"],
    "year": 2024,
    "month": 1
  }'
```

---

## 🧪 Testing the System

Run the test suite to verify everything works:

```bash
python test_system.py
```

This will test:
- ✅ Model loading
- ✅ Supported crops
- ✅ Crop horizons
- ✅ Feature engineering
- ✅ Price predictions

---

## 📈 Model Performance

| Metric | Value |
|--------|-------|
| **Model** | LightGBM Regressor |
| **Test R²** | 0.81 |
| **Test MAPE** | 19-20% |
| **Validation** | Time-based (no leakage) |
| **Training Data** | 2005-2021 |
| **Validation** | 2022 |
| **Test** | 2023+ |

---

## 🗂️ Data Sources

| Type | Source | Status |
|------|--------|--------|
| **Mandi Prices** | data.gov.in Agmarknet API | ✅ Integrated |
| **Weather** | Open-Meteo Archive API | ✅ Integrated |
| **NDVI** | Google Earth Engine | ⚠️ Optional (requires auth) |

---

## 🌾 Supported Crops (45+)

**Vegetables:** Beans, Beetroot, Brinjal, Cabbage, Capsicum, Carrot, Cauliflower, Tomato, etc.

**Cereals:** Wheat, Maize

**Cash Crops:** Cotton, Tobacco, Garlic, Onion, Groundnut

**Fruits:** Apple, Banana, Guava, Mango, Orange, Papaya, Pomegranate

**Others:** Castor Seed, Dry Chillies, Green Peas, etc.

Full list: `GET /crops` endpoint

---

## 📍 Supported Districts (33)

Ahmedabad, Amreli, Anand, Arvalli, Banaskantha, Bharuch, Bhavnagar, Botad, Chhota Udaipur, Dahod, Dang, Devbhoomi Dwarka, Gandhinagar, Gir Somnath, Jamnagar, Junagadh, Kheda, Kutch, Mahisagar, Mehsana, Morbi, Narmada, Navsari, Panchmahals, Patan, Porbandar, Rajkot, Sabarkantha, Surat, Surendranagar, Tapi, Vadodara, Valsad

---

## 🎓 How It Works

### 1. **Harvest-Window Target**
Instead of predicting next month's price, the model predicts:
```
Harvest Price = Average price in (month + horizon) and (month + horizon + 1)
```

### 2. **Crop-Specific Horizons**
Each crop has a biologically accurate growth period:
- Garlic: 6 months
- Wheat: 5 months
- Cabbage: 4 months
- Cotton: 6 months

### 3. **Log-Return Transformation**
```
Target = log(future_price / current_price)
Predicted Price = current_price * exp(predicted_return)
```

This ensures:
- Mean reversion handling
- Stability
- Better generalization

### 4. **Feature Engineering**
- Lag features (1, 3, 6, 12 months)
- Rolling statistics (3, 6 months)
- Momentum indicators
- Volatility measures
- Climate anomalies
- Seasonality (sin/cos encoding)

---

## 🚀 Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- AWS EC2 deployment
- Google Cloud Run
- Azure App Service
- Docker containerization
- Kubernetes orchestration
- SSL/HTTPS setup
- Monitoring & logging

---

## 🔐 Security Notes

1. **Never commit `.env` to git** - Contains API keys
2. **Use HTTPS in production** - Encrypt all traffic
3. **Implement rate limiting** - Prevent API abuse
4. **Restrict CORS** - Only allow known domains
5. **Use secret managers** - AWS Secrets Manager, Azure Key Vault, etc.

---

## 📞 Next Steps

### Immediate
1. ✅ Test the system: `python test_system.py`
2. ✅ Start the API: `start.bat` or `./start.sh`
3. ✅ Open web interface: `frontend/index.html`
4. ✅ Explore API docs: `http://localhost:8000/docs`

### Short-term
- [ ] Add your data.gov.in API key to `.env`
- [ ] Test with real historical data
- [ ] Customize the frontend styling
- [ ] Set up monitoring

### Long-term
- [ ] Deploy to cloud (AWS/GCP/Azure)
- [ ] Set up automated retraining
- [ ] Add SMS/WhatsApp notifications
- [ ] Build mobile app
- [ ] Add Gujarati language support

---

## 💡 Tips

### Performance
- API response time: ~100-300ms per prediction
- Batch predictions: Use `/compare` endpoint
- Cache predictions for frequently queried crops

### Accuracy
- Model works best with 18+ months of historical data
- Accuracy degrades for very volatile periods
- Consider ensemble predictions for critical decisions

### Data Freshness
- Update historical data monthly
- Retrain model quarterly
- Monitor prediction accuracy over time

---

## 🤝 Contributing

Want to improve the system?

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📧 Support

- **Documentation**: See README.md, API_USAGE.md, DEPLOYMENT.md
- **API Issues**: Check `/health` endpoint
- **Model Issues**: Run `test_system.py`
- **Questions**: Open an issue in the repository

---

## 🎉 You're All Set!

Your Gujarat Crop Price Forecasting System is ready to help farmers make informed decisions about which crops to grow.

**Start the system and make your first prediction! 🌾**

```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

Then visit: **http://localhost:8000/docs**

---

**Built with:** Python • FastAPI • LightGBM • Scikit-learn • Pandas • NumPy  
**Data:** data.gov.in • Open-Meteo • Google Earth Engine

---

*Disclaimer: This system provides forecasts based on historical data. Actual prices may vary. Use as one of many factors in decision-making.*
