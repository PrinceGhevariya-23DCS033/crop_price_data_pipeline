---
title: Gujarat Crop Price Forecasting
emoji: 🌾
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: mit
---

# 🌾 Gujarat Crop Price Forecasting System

Predict harvest-window prices for 45+ crops across 33 districts in Gujarat using machine learning models trained on historical market data, weather patterns, and satellite vegetation indices.

## 🎯 What Does It Do?

This system helps farmers and agricultural planners make informed cultivation decisions by predicting crop prices at harvest time based on:

- **Current Market Prices** - Latest mandi (market) prices
- **Weather Patterns** - Monthly rainfall data
- **Vegetation Health** - NDVI (Normalized Difference Vegetation Index) from satellite imagery
- **Crop Growth Cycles** - Growth horizon-aware predictions (e.g., wheat takes 4-5 months from sowing to harvest)

## 🚀 How to Use

1. **Select a Crop** - Choose from 45+ supported crops (Wheat, Cotton, Onion, etc.)
2. **Select a District** - Choose from 33 Gujarat districts
3. **Get Prediction** - Receive a price forecast for the harvest window with expected return %

### Example Use Case

> *"I'm a farmer in Ahmedabad planning to grow Wheat. What will the price be at harvest?"*

The system will:
1. Look at current wheat prices in Ahmedabad
2. Check rainfall and vegetation health (NDVI)
3. Apply ML model trained on 15+ years of data
4. Predict price 4-5 months ahead (wheat's growth cycle)
5. Show expected return % to help you decide

## 📊 Supported Crops

**Cereals:** Wheat, Maize, Bajra  
**Pulses:** Green Peas, Moath Dal, Rajgir  
**Oilseeds:** Groundnut, Mustard, Castor Seed, Guar  
**Spices:** Garlic, Onion, Green Chilli, Dry Chillies, Methi Seeds, Soanf  
**Vegetables:** Tomato, Potato, Cabbage, Cauliflower, Brinjal, Capsicum, Carrot, Beetroot  
**Fruits:** Mango, Banana, Pomegranate, Guava, Apple, Orange, Papaya, Watermelon  
**Cash Crops:** Cotton, Tobacco  
**And more...**

## 🗺️ Covered Districts

Ahmedabad, Amreli, Anand, Aravalli, Banaskantha, Bharuch, Bhavnagar, Botad, Chhota Udaipur, Dahod, Dang, Devbhoomi Dwarka, Gandhinagar, Gir Somnath, Jamnagar, Junagadh, Kheda, Kutch, Mahisagar, Mehsana, Morbi, Narmada, Navsari, Panchmahal, Patan, Porbandar, Rajkot, Sabarkantha, Surat, Surendranagar, Tapi, Vadodara, Valsad

## 🔬 Technology

- **ML Models:** XGBoost with lag and rolling features
- **Data Sources:**
  - Mandi Prices: data.gov.in (Agmarknet API)
  - Weather: Open-Meteo API
  - NDVI: Google Earth Engine (MODIS satellite)
- **Framework:** Gradio + FastAPI
- **Deployment:** Monthly cached data for fast predictions

## 📅 Data Freshness

Data is updated **monthly** (around 20-25th) when NDVI satellite data becomes available. This ensures:
- ✅ Predictions are based on recent conditions
- ✅ Sub-second response times (no real-time API calls)
- ✅ Reliable, consistent performance

**Current Cache Period:** Check the "Data Status" tab in the app

## 📈 Performance

- **Prediction Speed:** < 0.5 seconds
- **Coverage:** 45 crops × 33 districts = 1,485 combinations
- **Model Type:** Growth horizon-aware (crop-specific)
- **Training Data:** 15+ years of historical data

## ⚠️ Limitations

- **Forecasts, not guarantees** - Actual prices may vary due to market dynamics
- **Monthly updates** - Not real-time (data updated 20-25th each month)
- **Best for major crops** - More data = better predictions
- **Gujarat-specific** - Models trained on Gujarat data only

## 🎓 Model Details

### Features Used
- Current price (lag features)
- Month and year (temporal patterns)
- Monthly rainfall (sum and mean)
- NDVI (vegetation health)
- Days traded (market activity)
- Rolling price averages (3, 6, 12 months)
- District (location-specific patterns)

### Target
- Modal price at harvest window (growth horizon months ahead)

### Model Training
- Algorithm: XGBoost Regressor
- Cross-validation: Time-series aware
- Evaluation: MAE, RMSE, R²

## 📖 Use Cases

1. **Farmers:** Decide which crops to plant based on expected returns
2. **Agricultural Officers:** Plan district-level crop promotion programs
3. **Traders:** Anticipate market trends for procurement
4. **Researchers:** Study price patterns and volatility
5. **Students:** Learn about agricultural forecasting

## 🛠️ Technical Details

This system uses a **monthly cache architecture** to optimize performance:

```python
Monthly Update (20-25th) → Fetch Data → Cache Locally → Deploy to HF
   ↓
Users Get Predictions ← Cache Lookup (fast!) ← Gradio App
```

Benefits:
- 10-100x faster than real-time API calls
- No API rate limits or authentication issues
- Predictable, reliable performance
- Lower infrastructure costs

## 📊 Example Prediction

```
Crop: Wheat
District: Ahmedabad
Current Month: February 2024
Current Price: ₹2,850 per quintal
Growth Horizon: 4 months

→ Predicted Harvest Price (June 2024): ₹3,120 per quintal
→ Expected Return: +9.47%
→ Recommendation: Positive outlook ✅
```

## 🔄 Updates

- **Monthly Data:** 20-25th of each month
- **Model Retraining:** Annually with new year's data
- **New Features:** As needed based on feedback

## 📝 Citation

If you use this system in research, please cite:

```bibtex
@software{gujarat_crop_price_forecast,
  title={Gujarat Crop Price Forecasting System},
  author={Your Name},
  year={2024},
  url={https://huggingface.co/spaces/YOUR_USERNAME/crop-price-forecast}
}
```

## 📞 Contact & Feedback

- **Issues/Suggestions:** [GitHub Issues](https://github.com/YOUR_REPO/issues)
- **Email:** your-email@example.com
- **Community:** [Hugging Face Discussions](https://huggingface.co/spaces/YOUR_USERNAME/crop-price-forecast/discussions)

## 📜 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Data Providers:** data.gov.in, Open-Meteo, Google Earth Engine
- **Farmers of Gujarat** for domain knowledge
- **Agricultural Department, Gujarat** for support

---

**Developed with ❤️ for farmers and agricultural community of Gujarat**

*Empowering data-driven decisions for sustainable agriculture*
