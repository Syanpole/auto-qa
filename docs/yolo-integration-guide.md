# YOLO Model Integration Guide
## Team Pacific Corporation - AUTO QA System

**Last Updated:** May 1, 2026  
**Version:** 2.0  
**Status:** Production Ready

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Model Management](#model-management)
3. [Export Pipeline](#export-pipeline)
4. [Deployment](#deployment)
5. [Real-Time Detection UI](#real-time-detection-ui)
6. [Admin Dashboard](#admin-dashboard)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Step 1: Upload Your YOLO Model

```bash
# Place your .pt model file in the project
cp /path/to/your/ic_defect.pt backend/models_registry/deployed_models/

# Upload via Django admin or API
curl -X POST http://localhost:8000/api/v1/training/ai-models/upload/ \
  -F "file=@backend/models_registry/deployed_models/ic_defect.pt" \
  -F "model_name=ic_defect_v1" \
  -F "version_tag=1.0.0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 2: Export to Production Formats

```python
# Python script to export YOLO model
from backend.apps.training.yolo_export_pipeline import export_model

results = export_model(
    pt_model_path="backend/models_registry/deployed_models/ic_defect.pt",
    output_dir="backend/models_registry/exports"
)

# Results show TensorRT is recommended for RTX 4090
print(results['exports']['tensorrt']['recommendation'])
# Output: ✓✓✓ BEST for RTX 4090 (fastest inference)
```

### Step 3: Activate and Deploy

```bash
# Activate model via API
curl -X POST http://localhost:8000/api/v1/training/ai-models/ic_defect_v1/activate/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Deploy to production
curl -X POST http://localhost:8000/api/v1/training/deployments/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_model_id": "model-uuid",
    "deployment_target": "production"
  }'
```

### Step 4: Run Real-Time Detection

Access the detection UI at: `http://localhost:3000/detection`

---

## Model Management

### Supported Model Formats

| Format | Use Case | Advantages | Performance |
|--------|----------|-----------|-------------|
| **PyTorch (.pt)** | Training & Fine-tuning | Full flexibility | Baseline |
| **ONNX** | Cross-platform | Universal compatibility | Good (90% of PT) |
| **TensorRT** | RTX GPU optimization | Fastest on NVIDIA GPU | **BEST (3-5x faster)** |
| **OpenVINO** | Intel CPU/VPU | CPU deployment | Good (depends on HW) |
| **TorchScript** | PyTorch applications | PyTorch ecosystem | Good |

### Model Lifecycle States

```
DRAFT → TRAINING → VALIDATED → PRODUCTION → [DEPRECATED/ARCHIVED]
```

**State Descriptions:**

- **DRAFT**: Initial upload, not ready for use
- **TRAINING**: Model undergoing training/fine-tuning
- **VALIDATED**: Tested and approved, ready for deployment
- **PRODUCTION**: Active model in use for inference
- **DEPRECATED**: Older model, phase-out in progress
- **ARCHIVED**: Historical record, not available for new deployments

### Django Model: AIModel

```python
class AIModel(TimeStampedModel):
    # Core identification
    model_uuid: UUID              # Unique identifier
    model_name: str               # e.g., "ic_defect_v1"
    version_tag: str              # e.g., "1.0.0"
    model_family: str             # e.g., "yolov8"
    
    # Defect detection capabilities
    defect_types: list            # ["scratch", "crack", "chip", "surface_defect"]
    
    # File storage paths
    pt_file_path: str             # Path to .pt file
    onnx_file_path: str           # Path to .onnx file
    tensorrt_file_path: str       # Path to .engine file
    
    # Performance metrics
    throughput_fps: float         # Max FPS
    inference_time_ms: float      # Avg latency
    metrics_json: dict            # mAP50, precision, recall, F1
    
    # Status
    status: str                   # draft, training, validated, production
    is_active: bool               # Currently active for inference
    deployed_at: datetime         # When moved to production
```

### File Storage Structure

```
backend/
├── models_registry/
│   ├── deployed_models/           # Production model files
│   │   ├── ic_defect_v1.pt
│   │   ├── ic_defect_v2.pt
│   │   └── rt_detr_ic.pt
│   │
│   ├── exports/                   # Exported optimized formats
│   │   ├── ic_defect_v1.onnx
│   │   ├── ic_defect_v1.engine    # TensorRT (RTX 4090)
│   │   └── export_results.json    # Benchmark comparison
│   │
│   └── benchmarks/                # Performance data
│       ├── ic_defect_v1_rtx4090.json
│       └── ic_defect_v1_cpu.json

ml-service/
├── models/
│   ├── active/                    # Currently loaded models
│   │   ├── ic_defect_v1.pt
│   │   └── ic_defect_v1.engine
│   └── benchmarks/                # Benchmark results
```

---

## Export Pipeline

### Automatic Export to TensorRT (Recommended)

TensorRT provides **3-5x faster inference** on NVIDIA RTX 4090 compared to PyTorch.

#### Export Script

```python
from backend.apps.training.yolo_export_pipeline import YOLOExportPipeline

# Initialize pipeline
pipeline = YOLOExportPipeline(
    pt_model_path="backend/models_registry/deployed_models/ic_defect.pt",
    output_dir="backend/models_registry/exports"
)

# Export to all formats with benchmarking
results = pipeline.export_all()

# Access results
print(f"TensorRT FPS: {results['exports']['tensorrt']['benchmark']['throughput_fps']}")
print(f"Recommendation: {results['exports']['tensorrt']['recommendation']}")
```

#### Export Output

```json
{
  "source_model": "ic_defect.pt",
  "exports": {
    "tensorrt": {
      "status": "completed",
      "file_path": "backend/models_registry/exports/ic_defect.engine",
      "file_size_mb": 45.2,
      "benchmark": {
        "inference_time_ms": 12.5,
        "throughput_fps": 80,
        "min_latency_ms": 11.8,
        "max_latency_ms": 13.2,
        "p95_latency_ms": 12.8,
        "memory_usage_mb": 2048,
        "backend": "TensorRT (GPU)",
        "hardware": "RTX 4090"
      },
      "recommendation": "✓✓✓ BEST for RTX 4090 (fastest inference)"
    },
    "onnx": {
      "status": "completed",
      "throughput_fps": 25,
      "recommendation": "Recommended for cross-platform compatibility"
    }
  }
}
```

### Export Formats Comparison

#### RTX 4090 Performance

| Format | FPS | Latency (ms) | Memory (MB) | File Size (MB) | Use Case |
|--------|-----|-------------|-----------|----------------|----------|
| **TensorRT** | **80** | **12.5** | 2048 | 45 | ⭐ Production (BEST) |
| PyTorch (.pt) | 20 | 50 | 1024 | 100 | Training/Development |
| ONNX | 25 | 40 | 512 | 95 | Cross-platform compatibility |
| OpenVINO | 60* | 17* | 1024 | 85 | *On CPU (different hardware) |

---

## Deployment

### Deployment Targets

```python
DEPLOYMENT_TARGETS = {
    "production": "Production QA lines (all stations)",
    "staging": "Testing/validation environment",
    "station_A": "Specific QA station",
    "station_B": "Specific QA station",
    "edge_device": "Jetson/TPU deployment"
}
```

### Deployment Workflow

```
1. Upload Model (.pt)
   ↓
2. Validate & Test (Draft state)
   ↓
3. Export to TensorRT
   ↓
4. Benchmark & Compare
   ↓
5. Change Status to "Production"
   ↓
6. Activate Model
   ↓
7. Deploy to Target (production/station)
   ↓
8. Monitor Performance
   ↓
9. [Rollback if needed] or [Mark previous as Deprecated]
```

### API Endpoints

#### Upload Model
```bash
POST /api/v1/training/ai-models/upload/

Request:
{
  "file": <binary model file>,
  "model_name": "ic_defect_v1",
  "version_tag": "1.0.0",
  "framework": "ultralytics",
  "defect_types": ["scratch", "crack", "chip", "surface_defect"]
}

Response:
{
  "model_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "model_name": "ic_defect_v1",
  "version_tag": "1.0.0",
  "status": "draft",
  "is_active": false
}
```

#### Activate Model
```bash
POST /api/v1/training/ai-models/{model_uuid}/activate/

Response:
{
  "status": "activated",
  "model": "ic_defect_v1",
  "is_active": true
}
```

#### Deploy Model
```bash
POST /api/v1/training/deployments/

Request:
{
  "ai_model_id": "550e8400-e29b-41d4-a716-446655440000",
  "deployment_target": "production"
}

Response:
{
  "id": "deployment-uuid",
  "status": "active",
  "deployment_target": "production",
  "deployed_at": "2026-05-01T14:33:29Z"
}
```

#### List Available Models
```bash
GET /api/v1/training/ai-models/

Response:
{
  "count": 3,
  "results": [
    {
      "model_uuid": "...",
      "model_name": "ic_defect_v1",
      "version_tag": "1.0.0",
      "status": "production",
      "is_active": true,
      "throughput_fps": 80,
      "inference_time_ms": 12.5
    }
  ]
}
```

---

## Real-Time Detection UI

Access at: `http://localhost:3000/detection`

### Features

#### Live Camera Feed
- Real-time video from industrial camera
- Hardware-accelerated rendering
- Touch-screen friendly interface

#### Defect Detection
- Bounding box visualization
- Confidence scores per detection
- Defect class labels (scratch, crack, chip, surface_defect)
- Color-coded severity

#### Configuration Panel
- **Station Selection**: Choose QA station
- **Product Selection**: Choose product to inspect
- **Model Selection**: Choose AI model (admin can restrict per role)
- **Confidence Threshold**: Adjust sensitivity (0.5-0.99)
- **Inference Rate**: Control FPS (0.1-30 FPS)

#### Operator Actions
- **✓ Accept (Pass)**: Product passes inspection
- **🔧 Rework**: Product needs rework
- **✕ Scrap/Waste**: Product should be discarded

#### Inspection History
- Last 50 inspections
- Pass/reject summary
- Defect count per inspection
- Timestamp tracking

### Real-Time Inference API

```bash
POST /api/v1/ai/infer

Request:
{
  "image_base64": "base64_encoded_image_data",
  "station_id": "Station-A",
  "product_id": "IC_001",
  "model_name": "ic_defect_v1",
  "confidence_threshold": 0.85
}

Response:
{
  "status": "success",
  "pass_fail_status": "REJECT",
  "detection_count": 2,
  "detections": [
    {
      "class_id": 0,
      "class_name": "scratch",
      "confidence": 0.92,
      "bbox": [120, 80, 200, 150]
    },
    {
      "class_id": 2,
      "class_name": "chip",
      "confidence": 0.87,
      "bbox": [400, 200, 480, 280]
    }
  ],
  "inference_time_ms": 12.5,
  "model_used": "ic_defect_v1",
  "timestamp": "2026-05-01T14:35:00Z"
}
```

---

## Admin Dashboard

Access at: `http://localhost:3000/admin/models`

### Permissions (Super Admin Only)

### Tabs

#### Models Tab
- View all models with status
- Activate/Deactivate models
- Export to alternative formats
- Deploy to production
- Delete archived models
- View model metrics (FPS, latency, accuracy)

#### Exports Tab
- List all exported models
- View export status and benchmarks
- Download exported files
- Compare performance across formats

#### Deployments Tab
- Active deployments by target
- Deployment status (pending, active, inactive, rolled_back)
- Inference request counts
- Error tracking

#### Benchmarks Tab
- Hardware-specific benchmarks
- Performance comparison matrix
- Historical benchmark data
- Identify optimization opportunities

---

## API Reference

### ML Service Endpoints

#### Health Check
```bash
GET /health

Response:
{
  "status": "ok",
  "service": "yolo-ml-service",
  "active_models": 2,
  "gpu_available": true
}
```

#### List Models
```bash
GET /models

Response:
{
  "models": ["ic_defect_v1", "ic_defect_v2_optimized"],
  "total": 2
}
```

#### Load Model
```bash
POST /v1/models/load

Request:
{
  "model_path": "backend/models_registry/deployed_models/ic_defect.engine",
  "model_name": "ic_defect_v1"
}

Response:
{
  "status": "loaded",
  "model": "ic_defect_v1",
  "load_time_seconds": 2.3,
  "is_active": true
}
```

#### Single Inference
```bash
POST /v1/infer

Request:
{
  "image_base64": "...",
  "model_name": "ic_defect_v1",
  "confidence_threshold": 0.85
}

Response:
{
  "status": "success",
  "pass_fail_status": "PASS",
  "detection_count": 0,
  "detections": [],
  "inference_time_ms": 12.5,
  "model_used": "ic_defect_v1"
}
```

#### Batch Inference
```bash
POST /v1/infer/batch

Request:
{
  "images": [
    "base64_image_1",
    "base64_image_2"
  ],
  "model_name": "ic_defect_v1",
  "confidence_threshold": 0.85
}

Response:
{
  "status": "completed",
  "results": [...],
  "total_processed": 2
}
```

#### Benchmark
```bash
POST /v1/benchmark

Request:
{
  "model_name": "ic_defect_v1",
  "num_runs": 100
}

Response:
{
  "model": "ic_defect_v1",
  "num_runs": 100,
  "mean_latency_ms": 12.5,
  "p95_latency_ms": 13.2,
  "throughput_fps": 80,
  "hardware": "GPU"
}
```

---

## Troubleshooting

### Model Loading Issues

**Problem**: "Model file not found"
```
Solution:
1. Verify file path is correct
2. Check file permissions (chmod 644 model.pt)
3. Ensure model format is supported (.pt, .onnx, .engine)
```

**Problem**: "CUDA out of memory"
```
Solution:
1. Reduce batch size
2. Use TensorRT with FP16 (half precision)
3. Offload to CPU if GPU memory is limited
4. Consider using ONNX with smaller quantization
```

### Inference Performance Issues

**Problem**: "Low FPS / High Latency"
```
Solution:
1. Use TensorRT export (3-5x faster)
2. Enable GPU acceleration (check CUDA)
3. Reduce image resolution or batch size
4. Check system resource usage (nvidia-smi)
```

**Problem**: "Inaccurate detections"
```
Solution:
1. Adjust confidence_threshold (try 0.75-0.90)
2. Verify model was trained on similar data
3. Check for model drift - retrain if needed
4. Review logs for false positives
```

### Deployment Issues

**Problem**: "Model not accessible to operators"
```
Solution:
1. Check model status (must be "production")
2. Verify ModelAccess permissions granted
3. Check StationModelAssignment for station/product
4. Review audit logs for permission errors
```

### Docker Issues

**Problem**: "ML service fails to start"
```
Solution:
# Check logs
docker compose logs ml-service

# Rebuild with verbose output
docker compose build ml-service --no-cache

# Common fixes
1. Install NVIDIA Docker: nvidia-docker --version
2. Check CUDA availability: nvidia-smi
3. Verify GPU pass-through in compose
```

---

## Performance Optimization

### Hardware Recommendations

**GPU Deployment (Recommended)**
- NVIDIA RTX 4090: 80 FPS per model
- NVIDIA RTX 3090: 60 FPS per model
- NVIDIA A100: 120 FPS per model

**CPU Deployment**
- Intel Xeon (32 cores): 8-15 FPS
- AMD EPYC (32 cores): 10-18 FPS
- NOT recommended for real-time production

### Model Selection by Use Case

| Use Case | Format | Reasoning |
|----------|--------|-----------|
| High-speed production line (>100/min) | TensorRT | Maximum FPS |
| Edge device (Jetson) | ONNX or TensorRT | Lighter weight |
| Cross-platform compatibility | ONNX | Universal support |
| Rapid iteration/training | PyTorch | Full flexibility |

### Optimization Tips

1. **Export to TensorRT**: 3-5x speed improvement
2. **Use FP16 precision**: Trade minimal accuracy for speed
3. **Batch processing**: 1.5x faster for multiple images
4. **Resolution tuning**: Lower resolution = faster, but less accurate
5. **Model pruning**: Remove unnecessary neurons

---

## Monitoring & Logging

### Audit Trail

All model operations are logged:
- Model upload/delete
- Format exports
- Deployments/rollbacks
- Permission changes
- Inference statistics

Access audit logs: `/api/v1/audit/logs/?action_type=model_deployed`

### Metrics Collection

Real-time metrics available via:
- Django ORM query stats
- ML service `/v1/stats` endpoint
- Prometheus metrics (if enabled)

---

## Support & Questions

For issues or questions:
1. Check this guide's Troubleshooting section
2. Review audit logs and error messages
3. Contact Team Pacific Corporation support
4. Reference model version and deployment target

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | May 1, 2026 | Added TensorRT export, real-time UI, admin dashboard |
| 1.0 | April 15, 2026 | Initial YOLO integration |

---

**Last Updated:** May 1, 2026  
**Maintained By:** Team Pacific Corporation  
**Classification:** Internal Use Only
