# Production YOLO Model Setup & Integration Guide

This guide walks through loading the `tpcyolov26nv21gs.pt` model as the production inference engine for IC defect detection.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Setup Instructions](#setup-instructions)
4. [Model Registration](#model-registration)
5. [API Endpoints](#api-endpoints)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Start ML Service
```bash
cd "C:\Users\TPC-USER\Desktop\TPC PROJECT\ml-service"
.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 2. Load Production Model (Backend)
```bash
cd "C:\Users\TPC-USER\Desktop\TPC PROJECT\backend"
.venv\Scripts\Activate.ps1

# Run management command to load and register model
python manage.py load_production_model
```

### 3. Run Integration Tests
```bash
cd "C:\Users\TPC-USER\Desktop\TPC PROJECT\ml-service"
python scripts/test_integration.py
```

---

## Architecture Overview

### Components

1. **ML Service (FastAPI)** - `ml-service/`
   - YOLO model inference engine
   - RESTful API for model loading, inference, and management
   - Runs on port 8001

2. **Backend (Django)** - `backend/`
   - Model registry and lifecycle management
   - Inference audit logging to database
   - Permission and role-based access control
   - User-facing API endpoints

3. **Model Registry** - `backend/apps/ai/model_registry.py`
   - In-memory cache of active models
   - Thread-safe singleton for model configuration

4. **Database Models** - `backend/apps/ai/models.py`
   - `InferenceModel`: Tracks registered models and versions
   - `InferenceAuditLog`: Audit trail of all inference requests

### Data Flow

```
Frontend/Client
    ↓
[Django API] → resolve_authorized_inference()
    ↓
[Model Registry] → get_active_model() → "ic_defect_v1"
    ↓
[HTTP POST] → ML Service /v1/infer
    ↓
[FastAPI] → YOLOModelManager.infer()
    ↓
[YOLO Model] → Run inference on image
    ↓
[InferenceResponse] → Return detections + verdict
    ↓
[Audit Log] → Store in InferenceAuditLog table
    ↓
[Response] → Return to client
```

---

## Setup Instructions

### Prerequisites

- Python 3.10+ (venv for each service)
- Django 4.2+ with PostgreSQL/SQLite
- PyTorch (CPU or GPU)
- All dependencies listed in `requirements.txt`

### Step 1: ML Service Setup

```bash
# Navigate to ML service
cd "C:\Users\TPC-USER\Desktop\TPC PROJECT\ml-service"

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies (CPU version)
pip install --upgrade pip
pip install -r requirements.txt
pip install torch==2.11.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Or GPU version (replace with your CUDA version, e.g., cu121)
pip install torch==2.11.0+cu121 --index-url https://download.pytorch.org/whl/cu121
```

### Step 2: Backend Setup

```bash
# Navigate to backend
cd "C:\Users\TPC-USER\Desktop\TPC PROJECT\backend"

# Create/activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements/dev.txt  # or prod.txt for production

# Run migrations to create database tables
python manage.py migrate
```

### Step 3: Verify ML Service is Running

```bash
# In ML service terminal
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Step 4: Load Production Model

```bash
# In backend terminal
python manage.py load_production_model
```

Expected output:
```
Loading model from: C:\Users\TPC-USER\Desktop\TPC PROJECT\backend\models_registry\deployed_models\tpcyolov26nv21gs.pt
✓ Model loaded in ML service: loaded
✓ Model registered in backend: ic_defect_v1
✓ Model activated as production model
✓ Model verified in ML service: ic_defect_v1
  Classes: X detected
  Device: CPU

======================================================================
MODEL LOADED SUCCESSFULLY
======================================================================
Model Name: ic_defect_v1
Model Path: ...tpcyolov26nv21gs.pt
Active: True
Confidence Threshold: 0.85
IOU Threshold: 0.50
======================================================================
```

---

## Model Registration

### Manual Registration (if not using management command)

```python
from apps.ai.model_loader import ModelLoaderService

# Load and register model
result = ModelLoaderService.load_model_from_file(
    file_path=r"C:\Users\TPC-USER\Desktop\TPC PROJECT\backend\models_registry\deployed_models\tpcyolov26nv21gs.pt",
    model_name="ic_defect_v1",
    description="Production YOLO model for IC defect detection",
    confidence_threshold=0.85,
    iou_threshold=0.50,
    version="2.6n",
    architecture="YOLOv8n",
    is_active=True  # Set as active
)

print(result)
# Output:
# {
#     "status": "loaded",
#     "model_name": "ic_defect_v1",
#     "model_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
#     "file_path": "...",
#     "file_size_mb": 6.2,
#     "is_active": True,
#     "created": True
# }
```

### Replace Existing Active Model

```python
from apps.ai.model_loader import ModelLoaderService

# Load new model
ModelLoaderService.load_model_from_file(
    file_path=r"C:\path\to\new_model.pt",
    model_name="ic_defect_v2",
    is_active=False  # Don't activate yet
)

# Test new model...
# Then activate when ready
ModelLoaderService.activate_model("ic_defect_v2")
```

---

## API Endpoints

### ML Service (FastAPI) - Port 8001

#### Health & Status
```
GET /health
GET /models
GET /models/{model_name}
```

#### Inference
```
POST /v1/infer
POST /v1/infer/batch
POST /v1/infer/stream
```

#### Model Management
```
POST /v1/models/load
POST /v1/models/activate
POST /v1/models/deactivate
POST /v1/models/unload
```

#### Benchmarking
```
POST /v1/benchmark
GET /v1/stats
POST /v1/stats/reset
```

---

### Backend (Django) - Port 8000

#### Inference
```
POST /api/ai/inference/realtime  # Single image
POST /api/ai/inference/batch      # Multiple images
POST /api/ai/ai/infer            # Alias endpoint
POST /api/ai/ai/snapshot         # Store snapshot event
POST /api/ai/ai/disposition      # Record operator decision
```

#### Model Management (Admin Only)
```
GET  /api/ai/models/list         # List all models
GET  /api/ai/models/active       # Get active model info
POST /api/ai/models/activate     # Activate model (requires {"model_name": "..."})
```

#### Statistics
```
GET /api/ai/ai/stats             # User inference statistics
```

---

## Testing

### Integration Test Suite

```bash
cd "C:\Users\TPC-USER\Desktop\TPC PROJECT\ml-service"
python scripts/test_integration.py
```

This runs the complete test pipeline:
1. ✓ ML Service Health Check
2. ✓ Load Model
3. ✓ Verify Model
4. ✓ List Models
5. ✓ Single Inference
6. ✓ Batch Inference
7. ✓ Service Stats

### Manual API Testing (curl examples)

#### Load Model
```bash
curl -X POST "http://localhost:8001/v1/models/load?model_path=C%3A%5CUsers%5CTPC-USER%5CDesktop%5CTPC%20PROJECT%5Cbackend%5Cmodels_registry%5Cdeployed_models%5Ctpcyolov26nv21gs.pt&model_name=ic_defect_v1"
```

#### Single Inference (with file upload)
```bash
curl -X POST -F "file=@C:\path\to\image.jpg" http://localhost:8001/v1/infer/stream
```

#### Get Active Model (Backend)
```bash
curl -X GET "http://localhost:8000/api/ai/models/active" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Run Inference (Backend)
```bash
curl -X POST "http://localhost:8000/api/ai/inference/realtime" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "image_base64": "...",
    "station_id": "Station-A",
    "product_id": "IC_001",
    "confidence_threshold": 0.85
  }'
```

### Python Client Example

```python
import requests
import base64
from pathlib import Path

# Configuration
ML_SERVICE_URL = "http://localhost:8001"
BACKEND_URL = "http://localhost:8000"
BACKEND_TOKEN = "your_auth_token"

# Load image
image_path = Path("path/to/image.jpg")
with open(image_path, "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")

# Run inference via backend
headers = {
    "Authorization": f"Bearer {BACKEND_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "image_base64": image_b64,
    "station_id": "Station-A",
    "product_id": "IC_001",
    "confidence_threshold": 0.85
}

response = requests.post(
    f"{BACKEND_URL}/api/ai/inference/realtime",
    json=payload,
    headers=headers,
    timeout=30
)

result = response.json()
print(f"Verdict: {result['pass_fail_status']}")
print(f"Detections: {result['detection_count']}")
print(f"Latency: {result['inference_time_ms']} ms")
```

---

## Troubleshooting

### Model Not Loading

**Problem:** "Model file not found"
- **Solution:** Verify absolute path is correct and file exists
  ```bash
  ls "C:\Users\TPC-USER\Desktop\TPC PROJECT\backend\models_registry\deployed_models\tpcyolov26nv21gs.pt"
  ```

**Problem:** "ML service unavailable"
- **Solution:** Ensure ML service is running on port 8001
  ```bash
  curl http://localhost:8001/health
  ```

### Slow Inference

**Problem:** Inference taking >5 seconds
- **Solution:** Check if GPU is available
  ```bash
  python -c "import torch; print('GPU:', torch.cuda.is_available())"
  ```
  - If False, consider installing GPU PyTorch or accepting CPU latency

### Database Audit Not Logging

**Problem:** InferenceAuditLog table is empty
- **Solution:** Ensure migrations have been run
  ```bash
  python manage.py migrate
  ```
  - Check that Django DEBUG=True in settings (or check logs)
  - Verify inference requests have correct model_name

### Model Not Active

**Problem:** Inferences still use old model
- **Solution:** Verify active model
  ```bash
  python manage.py shell
  >>> from apps.ai.model_loader import ModelLoaderService
  >>> ModelLoaderService.get_active_model()
  ```
  - If not correct, activate:
    ```python
    >>> ModelLoaderService.activate_model("ic_defect_v1")
    ```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Model loaded and active (`load_production_model` executed)
- [ ] Database migrations applied (`python manage.py migrate`)
- [ ] Integration tests pass (`python scripts/test_integration.py`)
- [ ] Inference latency acceptable (<2s on production hardware)
- [ ] Audit logging verified (check InferenceAuditLog table)
- [ ] Backup of model file stored
- [ ] SSL/TLS configured for API endpoints
- [ ] Environment variables set (ML_SERVICE_URL, BACKEND_URL)

### Environment Variables

```
# .env file or server config
ML_SERVICE_URL=http://ml-service:8001          # Internal ML service URL
PRODUCTION_MODEL_PATH=/models/tpcyolov26nv21gs.pt  # Optional: override default path
DEBUG=False                                     # Production: False
ALLOWED_HOSTS=yourdomain.com                    # Set to actual domain
```

### Docker Deployment

See `docker-compose.yml` for full stack deployment with ML service + backend + database.

```bash
docker-compose up -d
```

This starts all services, automatically runs migrations, and loads the production model.

---

## Additional Resources

- [YOLO Documentation](https://docs.ultralytics.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Project README](../../README.md)

