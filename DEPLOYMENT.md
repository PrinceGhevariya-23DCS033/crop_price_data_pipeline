# Production Deployment Guide

## 🚀 Deployment Options

### Option 1: Local Server (Development/Testing)

**Requirements:**
- Python 3.8+
- 2GB RAM minimum
- Port 8000 available

**Steps:**
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` file with API keys
3. Run: `python src/api.py` or `./start.sh` (Linux/Mac) / `start.bat` (Windows)

**Access:**
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

---

### Option 2: Cloud Deployment (AWS, GCP, Azure)

#### AWS EC2

**1. Launch EC2 Instance**
```bash
# Amazon Linux 2 or Ubuntu 20.04+
# Instance type: t2.medium (2 vCPU, 4GB RAM)
# Security group: Allow inbound on ports 22, 80, 443, 8000
```

**2. SSH into instance and setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.8+
sudo apt install python3.8 python3-pip python3-venv -y

# Clone your repository
git clone <your-repo-url>
cd Crop_Price_V2

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your API keys
```

**3. Run with process manager (PM2 or systemd)**

Using **systemd**:
```bash
sudo nano /etc/systemd/system/crop-price-api.service
```

Add:
```ini
[Unit]
Description=Gujarat Crop Price Forecasting API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Crop_Price_V2/src
Environment="PATH=/home/ubuntu/Crop_Price_V2/venv/bin"
ExecStart=/home/ubuntu/Crop_Price_V2/venv/bin/python api.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable crop-price-api
sudo systemctl start crop-price-api
sudo systemctl status crop-price-api
```

**4. Setup Nginx reverse proxy**
```bash
sudo apt install nginx -y

sudo nano /etc/nginx/sites-available/crop-price-api
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/crop-price-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**5. SSL Certificate (Optional but recommended)**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

#### Google Cloud Platform (Cloud Run)

**1. Create Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY production_model/ ./production_model/
COPY processed/ ./processed/
COPY .env .env

EXPOSE 8000

CMD ["python", "src/api.py"]
```

**2. Build and deploy**
```bash
# Build image
gcloud builds submit --tag gcr.io/your-project-id/crop-price-api

# Deploy to Cloud Run
gcloud run deploy crop-price-api \
  --image gcr.io/your-project-id/crop-price-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi
```

---

#### Azure App Service

**1. Create App Service**
```bash
# Create resource group
az group create --name CropPriceRG --location eastus

# Create app service plan
az appservice plan create \
  --name CropPricePlan \
  --resource-group CropPriceRG \
  --sku B2 \
  --is-linux

# Create web app
az webapp create \
  --resource-group CropPriceRG \
  --plan CropPricePlan \
  --name crop-price-api \
  --runtime "PYTHON|3.9"
```

**2. Deploy code**
```bash
# Configure deployment
az webapp deployment source config-local-git \
  --name crop-price-api \
  --resource-group CropPriceRG

# Push code
git remote add azure <deployment-url>
git push azure main
```

---

### Option 3: Docker Container

**1. Create Dockerfile**
```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY production_model/ ./production_model/
COPY processed/ ./processed/

# Copy environment file
COPY .env .env

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "src/api.py"]
```

**2. Create docker-compose.yml**
```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: crop-price-api
    ports:
      - "8000:8000"
    environment:
      - DATA_GOV_API_KEY=${DATA_GOV_API_KEY}
    env_file:
      - .env
    volumes:
      - ./production_model:/app/production_model
      - ./processed:/app/processed
    restart: unless-stopped
    mem_limit: 2g
    cpus: 1

  nginx:
    image: nginx:alpine
    container_name: crop-price-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend:/usr/share/nginx/html
    depends_on:
      - api
    restart: unless-stopped
```

**3. Build and run**
```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Check logs
docker-compose logs -f api

# Stop
docker-compose down
```

---

### Option 4: Kubernetes (Production Scale)

**1. Create deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crop-price-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crop-price-api
  template:
    metadata:
      labels:
        app: crop-price-api
    spec:
      containers:
      - name: api
        image: your-registry/crop-price-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATA_GOV_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: data-gov-api-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: crop-price-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: crop-price-api
```

**2. Deploy**
```bash
kubectl apply -f deployment.yaml
kubectl get pods
kubectl get services
```

---

## 🔒 Security Best Practices

### 1. Environment Variables
```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use secret management in production
# AWS: AWS Secrets Manager
# GCP: Secret Manager
# Azure: Key Vault
```

### 2. API Key Protection
```python
# In production, use environment-based secrets
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("DATA_GOV_API_KEY")
```

### 3. HTTPS/SSL
```bash
# Always use HTTPS in production
# Use Let's Encrypt for free SSL certificates
certbot --nginx -d your-domain.com
```

### 4. Rate Limiting
```python
# Add to FastAPI app
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/predict")
@limiter.limit("10/minute")
async def predict():
    ...
```

### 5. CORS Configuration
```python
# Restrict CORS in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 📊 Monitoring & Logging

### 1. Application Logs
```python
# Add logging to api.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### 2. Performance Monitoring
```bash
# Use Prometheus + Grafana
pip install prometheus-fastapi-instrumentator

# In api.py
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### 3. Error Tracking
```bash
# Use Sentry
pip install sentry-sdk

# In api.py
import sentry_sdk

sentry_sdk.init(dsn="your-sentry-dsn")
```

---

## 🔄 Automated Retraining

**1. Create retraining script**
```python
# retrain.py
import schedule
import time

def retrain_model():
    # Load new data
    # Train model
    # Save to production_model/
    # Restart API
    pass

# Run weekly
schedule.every().sunday.at("02:00").do(retrain_model)

while True:
    schedule.run_pending()
    time.sleep(3600)
```

**2. Setup cron job**
```bash
# Crontab
0 2 * * 0 /home/user/Crop_Price_V2/venv/bin/python retrain.py
```

---

## 🧪 Testing Before Deployment

```bash
# Run system tests
python test_system.py

# Test API endpoints
pytest tests/

# Load testing
pip install locust
locust -f tests/locustfile.py --host=http://localhost:8000
```

---

## 📈 Performance Optimization

### 1. Caching
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def predict_cached(commodity, district, year, month):
    # Cache predictions for same inputs
    pass
```

### 2. Connection Pooling
```python
# For database connections
from sqlalchemy import create_engine, pool

engine = create_engine(
    "postgresql://user:pass@host/db",
    poolclass=pool.QueuePool,
    pool_size=10
)
```

### 3. Async Processing
```python
# For heavy I/O operations
from fastapi import BackgroundTasks

@app.post("/predict/async")
async def predict_async(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_prediction)
    return {"status": "processing"}
```

---

## 📞 Support & Maintenance

### Backup Strategy
```bash
# Daily backups
0 3 * * * tar -czf backup-$(date +\%Y\%m\%d).tar.gz production_model/ processed/
```

### Update Procedure
1. Test in development
2. Deploy to staging
3. Run integration tests
4. Blue-green deployment to production
5. Monitor for 24 hours

---

For questions, contact your DevOps team or open an issue in the repository.
