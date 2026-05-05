# YOLO Integration Deployment Guide

## Prerequisites

### System Requirements
- **OS**: Ubuntu 22.04 LTS or later
- **GPU**: NVIDIA RTX 4090 (or RTX 3090, A100, etc.)
- **CUDA**: 12.2 or later
- **cuDNN**: 8.x compatible with CUDA
- **Docker**: 24.0+
- **Docker Compose**: 2.20+

### NVIDIA Setup

```bash
# 1. Install NVIDIA GPU drivers
ubuntu-drivers devices
sudo ubuntu-drivers autoinstall
nvidia-smi  # Verify installation

# 2. Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# 3. Test NVIDIA Docker
docker run --rm --runtime=nvidia nvidia/cuda:12.2.2-runtime-ubuntu22.04 nvidia-smi
```

---

## Deployment Steps

### 1. Prepare Model Files

```bash
# Create model directory
mkdir -p backend/models_registry/deployed_models

# Copy your YOLO .pt model
cp /path/to/your/trained_model.pt \
   backend/models_registry/deployed_models/ic_defect_v1.pt

# Verify file
ls -lh backend/models_registry/deployed_models/
# ic_defect_v1.pt (100MB)
```

### 2. Export to TensorRT (Recommended)

```bash
# Create Python script
cat > export_model.py << 'EOF'
import sys
sys.path.insert(0, './backend')

from apps.training.yolo_export_pipeline import export_model

# Export model
results = export_model(
    pt_model_path="backend/models_registry/deployed_models/ic_defect_v1.pt",
    output_dir="backend/models_registry/exports"
)

# Print results
import json
print(json.dumps(results, indent=2))
EOF

# Run export (inside Docker or local environment)
python export_model.py

# Verify exports
ls -lh backend/models_registry/exports/
# ic_defect_v1.onnx (95MB)
# ic_defect_v1.engine (45MB)  <- TensorRT (best performance)
```

### 3. Build and Start Services

```bash
# Set environment variables
cp .env.example .env

# Edit .env with your settings
nano .env
# Required settings:
# - DB credentials
# - SECRET_KEY
# - ML_SERVICE_URL=http://ml-service:8001
# - CONFIDENCE_THRESHOLD=0.85

# Build Docker images
docker compose build

# Start services
docker compose up -d

# Verify services are running
docker compose ps
# STATUS should be "Up" for all services
```

### 4. Initialize Database

```bash
# Run migrations
docker compose exec backend python manage.py migrate

# Seed RBAC roles and permissions
docker compose exec backend python manage.py seed_rbac

# Create superuser (optional)
docker compose exec backend python manage.py createsuperuser
```

### 5. Load Model into ML Service

```bash
# Shell into ML service
docker compose exec ml-service bash

# Inside container:
python << 'EOF'
from app.yolo_model_manager import YOLOModelManager

manager = YOLOModelManager()

# Load TensorRT model (recommended)
result = manager.load_model(
    model_path="models/active/ic_defect_v1.engine",
    model_name="ic_defect_v1_tensorrt"
)
print(result)

# Or load PyTorch model
result = manager.load_model(
    model_path="models/active/ic_defect_v1.pt",
    model_name="ic_defect_v1_pytorch"
)
print(result)

# Activate model
manager.activate_model("ic_defect_v1_tensorrt")
print("Model activated!")
EOF

exit
```

### 6. Verify Deployment

```bash
# Health check
curl http://localhost:8000/health
# {"status": "ok"}

# ML service health
curl http://localhost:8001/health
# {"status": "ok", "service": "yolo-ml-service", ...}

# Test inference
curl -X POST http://localhost:8001/v1/infer \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "base64_encoded_test_image",
    "model_name": "ic_defect_v1_tensorrt",
    "confidence_threshold": 0.85
  }'

# Access frontend
# http://localhost:3000
```

---

## Production Deployment Checklist

- [ ] NVIDIA GPU drivers installed and verified
- [ ] Docker and Docker Compose installed
- [ ] Model files copied to `backend/models_registry/deployed_models/`
- [ ] Model exported to TensorRT format
- [ ] `.env` file configured with production secrets
- [ ] Docker images built successfully
- [ ] Database migrations applied
- [ ] RBAC roles seeded
- [ ] Model loaded into ML service
- [ ] Frontend accessible at http://localhost
- [ ] Backend API responding at /api/v1/
- [ ] Real-time detection UI working at /detection
- [ ] Admin dashboard accessible at /admin/models
- [ ] First defect detection tested end-to-end

---

## Troubleshooting Deployment

### GPU Not Available

```bash
# Check NVIDIA Docker runtime
docker run --rm --runtime=nvidia nvidia/cuda:12.2.2-runtime-ubuntu22.04 \
  nvidia-smi

# If fails, add runtime to daemon.json
sudo vim /etc/docker/daemon.json
# Add or modify:
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}

# Restart Docker
sudo systemctl restart docker
```

### Model Loading Fails

```bash
# Check model file is readable
ls -l backend/models_registry/deployed_models/

# Test model loading locally
python << 'EOF'
from ultralytics import YOLO
model = YOLO("backend/models_registry/deployed_models/ic_defect_v1.pt")
print("Model loaded successfully!")
EOF
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Test connection
docker compose exec backend python << 'EOF'
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()
print("Database connection OK!")
EOF
```

### ML Service Inference Slow

```bash
# Benchmark the model
curl -X POST http://localhost:8001/v1/benchmark \
  -H "Content-Type: application/json" \
  -d '{"model_name": "ic_defect_v1_tensorrt", "num_runs": 100}'

# Should show ~80 FPS for TensorRT on RTX 4090
# If lower, check:
# 1. GPU not being used (check nvidia-smi)
# 2. Model not optimized (use TensorRT export)
# 3. System resources limited (check memory/CPU)
```

---

## Performance Monitoring

### Monitor GPU Usage

```bash
# Real-time GPU monitoring
watch -n 1 'nvidia-smi'

# Expected output during inference:
# GPU 0: RTX 4090 - 2000/24000 MB | Processes: python (2000 MB)
```

### Monitor Service Health

```bash
# Check all services
docker compose ps

# View logs
docker compose logs -f backend    # Django backend
docker compose logs -f ml-service # ML inference service
docker compose logs -f frontend   # React frontend

# Database logs
docker compose logs -f postgres
```

### Performance Metrics

```bash
# Query API stats
curl http://localhost:8000/api/v1/ai/stats

# Response:
{
  "total_inferences": 1250,
  "pass_count": 980,
  "fail_count": 270,
  "pass_rate_percent": 78.4
}

# ML service stats
curl http://localhost:8001/v1/stats
```

---

## Backup and Recovery

### Backup Database

```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U autoqa autoqa_db > backup.sql

# Restore
docker compose exec -T postgres psql -U autoqa autoqa_db < backup.sql
```

### Backup Model Files

```bash
# Archive all models
tar -czf models_backup_$(date +%Y%m%d).tar.gz \
  backend/models_registry/

# Restore
tar -xzf models_backup_20260501.tar.gz
```

---

## Scaling Considerations

### Multi-Model Deployment

```python
# Load multiple models for load balancing
manager = YOLOModelManager()

manager.load_model("models/ic_defect_v1.engine", "ic_v1")
manager.load_model("models/ic_defect_v2.engine", "ic_v2")
manager.load_model("models/rt_detr_ic.engine", "rtdetr")

# Route requests based on station/product
if product in ["IC_001", "IC_002"]:
    manager.activate_model("ic_v1")
elif product == "IC_003":
    manager.activate_model("ic_v2")
```

### Multi-GPU Deployment

```bash
# Modify docker-compose.yml for multi-GPU
services:
  ml-service:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all  # Use all GPUs
              capabilities: [gpu]
```

---

## Security Best Practices

### API Authentication

```bash
# Generate API token
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "operator", "password": "password"}'

# Use token in requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/ai/stats
```

### Model File Permissions

```bash
# Restrict model file access
chmod 640 backend/models_registry/deployed_models/*.pt
chmod 640 backend/models_registry/exports/*.engine

# Set ownership
sudo chown root:docker backend/models_registry/
```

### Firewall Rules

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (Frontend)
sudo ufw allow 443/tcp   # HTTPS (if configured)
# Do NOT expose 8000 (API) or 8001 (ML service) externally
```

---

## Maintenance Schedule

### Daily
- Monitor GPU usage and inference latency
- Check error logs
- Verify all services are running

### Weekly
- Review defect detection accuracy
- Analyze false positives/negatives
- Update confidence thresholds if needed

### Monthly
- Export model performance benchmarks
- Review deployment metrics
- Plan model retraining if accuracy drifts
- Check system capacity

### Quarterly
- Full system backup
- Security audit
- Model versioning and archival
- Performance optimization review

---

## Support Contact

For deployment issues:
1. Check logs: `docker compose logs`
2. Review this guide
3. Contact: support@teamglac.com

**Deployment completed successfully!** 🎉

Your AUTO QA system is now ready for real-time IC defect detection using YOLO models.
