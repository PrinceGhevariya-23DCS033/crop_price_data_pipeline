╔══════════════════════════════════════════════════════════════════╗
║         HUGGING FACE SPACES - FASTAPI DEPLOYMENT                 ║
║         Gujarat Crop Price Forecasting API                       ║
╚══════════════════════════════════════════════════════════════════╝

📦 REQUIRED FILES FOR DEPLOYMENT
─────────────────────────────────────────────────────────────────

Upload these files to your HF Space repository:

✅ From this folder (deployments/huggingface_api/):
   • app.py                    (FastAPI application)
   • Dockerfile                (Container configuration)
   • requirements.txt          (Python dependencies)

✅ From main project (copy to HF Space):
   • src/                      (All Python modules)
   • production_model/         (Trained models - *.pkl files)
   • processed/                (Historical CSVs)
   • monthly_cache/            (Pre-generated cache - CRITICAL!)
   • district_latlon.csv       (District coordinates)

─────────────────────────────────────────────────────────────────

🚀 DEPLOYMENT STEPS
─────────────────────────────────────────────────────────────────

1. Create HF Space
   • Go to: https://huggingface.co/new-space
   • Choose: Docker SDK (NOT Gradio)
   • Hardware: CPU Basic (free tier)

2. Clone Repository
   git clone https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME
   cd SPACE_NAME

3. Setup Git LFS (for large files)
   git lfs install
   git lfs track "*.pkl"
   git lfs track "*.csv"
   git add .gitattributes

4. Copy Files
   cp ../Crop_Price_V2/deployments/huggingface_api/* .
   cp -r ../Crop_Price_V2/src .
   cp -r ../Crop_Price_V2/production_model .
   cp -r ../Crop_Price_V2/processed .
   cp -r ../Crop_Price_V2/monthly_cache .
   cp ../Crop_Price_V2/district_latlon.csv .

5. Commit & Push
   git add .
   git commit -m "Initial FastAPI deployment"
   git push

6. Wait for Build
   • HF will build Docker image (3-5 minutes)
   • Check logs for errors
   • API will be available at your Space URL

─────────────────────────────────────────────────────────────────

📡 API ENDPOINTS
─────────────────────────────────────────────────────────────────

Base URL: https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME

• GET  /                        - Health check
• GET  /health                  - Detailed health status
• GET  /docs                    - Interactive API docs
• GET  /api/crops               - List all crops
• GET  /api/districts           - List all districts
• GET  /api/cache-status        - Cache metadata
• POST /api/predict             - Make prediction (MAIN)
• GET  /api/crop/{name}/info    - Crop information

─────────────────────────────────────────────────────────────────

🔧 TESTING LOCALLY
─────────────────────────────────────────────────────────────────

Before deploying, test locally:

1. Build Docker image
   docker build -t crop-api .

2. Run container
   docker run -p 7860:7860 crop-api

3. Test API
   curl http://localhost:7860/health
   
   Open http://localhost:7860/docs for interactive testing

─────────────────────────────────────────────────────────────────

⚙️ CORS CONFIGURATION
─────────────────────────────────────────────────────────────────

Update app.py with your Vercel domain:

allow_origins=[
    "https://your-app.vercel.app",  # Your production domain
    "https://*.vercel.app",         # Vercel previews
]

Remove "*" in production for security!

─────────────────────────────────────────────────────────────────

🔄 MONTHLY UPDATES
─────────────────────────────────────────────────────────────────

Cache is updated automatically via GitHub Actions.
See: deployments/github_actions/monthly-cache-update.yml

Manual update:
1. Run update_monthly_cache.py locally
2. Copy monthly_cache/ to HF Space repo
3. Git push (HF will auto-rebuild)

─────────────────────────────────────────────────────────────────

✅ VERIFICATION CHECKLIST
─────────────────────────────────────────────────────────────────

After deployment:
[ ] Space builds successfully (no errors in logs)
[ ] GET /health returns "healthy"
[ ] GET /api/crops returns list of crops
[ ] POST /api/predict works with test data
[ ] CORS allows your Vercel domain
[ ] API response time < 1 second

─────────────────────────────────────────────────────────────────

📞 SUPPORT
─────────────────────────────────────────────────────────────────

HF Spaces Docker Docs: https://huggingface.co/docs/hub/spaces-sdks-docker
FastAPI Docs: https://fastapi.tiangolo.com/

═══════════════════════════════════════════════════════════════════
