╔══════════════════════════════════════════════════════════════════╗
║                  VERCEL FRONTEND DEPLOYMENT                      ║
║              React App - Crop Price Forecasting                  ║
╚══════════════════════════════════════════════════════════════════╝

📝 PLACEHOLDER FOR REACT FRONTEND
─────────────────────────────────────────────────────────────────

This folder is prepared for your React/MERN stack frontend.

When you create your React app, place it here and follow the
deployment guide below.

─────────────────────────────────────────────────────────────────

🎯 API INTEGRATION
─────────────────────────────────────────────────────────────────

Your React app will call the HF Space API:

API Base URL:
https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME

Example API call (React/JavaScript):

```javascript
// src/services/api.js

const API_BASE_URL = process.env.REACT_APP_API_URL || 
  'https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME';

export const predictPrice = async (commodity, district, year, month) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        commodity,
        district,
        year,
        month
      })
    });
    
    if (!response.ok) {
      throw new Error('Prediction failed');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const getCrops = async () => {
  const response = await fetch(`${API_BASE_URL}/api/crops`);
  return response.json();
};

export const getDistricts = async () => {
  const response = await fetch(`${API_BASE_URL}/api/districts`);
  return response.json();
};
```

─────────────────────────────────────────────────────────────────

🚀 VERCEL DEPLOYMENT
─────────────────────────────────────────────────────────────────

1. Create React app in this folder:
   npx create-react-app frontend
   cd frontend

2. Build your UI components

3. Add environment variable:
   Create .env file:
   REACT_APP_API_URL=https://huggingface.co/spaces/USER/SPACE

4. Install Vercel CLI:
   npm install -g vercel

5. Deploy:
   vercel

6. Set environment variables in Vercel dashboard

─────────────────────────────────────────────────────────────────

📦 RECOMMENDED REACT STRUCTURE
─────────────────────────────────────────────────────────────────

frontend/
├── src/
│   ├── components/
│   │   ├── PredictionForm.jsx
│   │   ├── ResultCard.jsx
│   │   └── CropSelector.jsx
│   ├── services/
│   │   └── api.js
│   ├── App.js
│   └── index.js
├── public/
├── package.json
└── .env

─────────────────────────────────────────────────────────────────

🔧 REQUIRED NPM PACKAGES
─────────────────────────────────────────────────────────────────

npm install axios          # HTTP client (alternative to fetch)
npm install react-query    # Data fetching & caching
npm install tailwindcss    # Styling (optional)

─────────────────────────────────────────────────────────────────

✅ TESTING API CONNECTION
─────────────────────────────────────────────────────────────────

Before building frontend, test API:

curl https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE/api/crops

Should return JSON array of crops.

─────────────────────────────────────────────────────────────────

📞 NEXT STEPS
─────────────────────────────────────────────────────────────────

1. Deploy FastAPI to HF Space first
2. Test API endpoints work
3. Create React app in this folder
4. Integrate API calls
5. Deploy to Vercel

═══════════════════════════════════════════════════════════════════
