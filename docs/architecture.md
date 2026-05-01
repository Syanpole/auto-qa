# Enterprise Architecture

## 1) Reference Architecture

```text
Industrial Cameras -> Station Edge Agent -> Inference Gateway (ML Service)
                                       -> Defect Verdict + Overlay
                                       -> Django API (events, metadata, rules)
                                       -> PostgreSQL + Object Storage
                                       -> Celery Workers (reports, retraining, ETL)
                                       -> React Dashboard + Alert Channels
```

## 2) Core Services
- Camera Ingestion Service
  - Pulls RTSP/USB streams or receives triggered stills
  - Normalizes image frames and metadata
  - Applies station-level buffering/backpressure controls
- Inference Service (ml-service)
  - Unified model interface for ESMD-YOLOv26n and RT-DETR
  - Model warm pools per station and batch queue support
  - Returns defect class, confidence, bbox/polygon, and heatmap
- QA Orchestrator (Django)
  - Applies station and product-specific thresholds
  - Saves defect events and routes nonconforming units
  - Publishes live state to dashboard channels
- Training Pipeline
  - Dataset curation, labeling references, versioning, lineage
  - Scheduled or trigger-based fine tuning
  - Validation gates and model promotion workflow
- Audit and Reporting
  - Immutable event logging
  - Shift reports, lot-level metrics, and CSV/PDF exports

## 3) Runtime Modes
- Real-time mode
  - Single-unit inspection with deterministic latency targets
- Batch mode
  - Multi-station image batches for offline validation and calibration
- Training mode
  - Controlled resource isolation for retraining jobs

## 4) Scalability Model
- Horizontal scale
  - Add inference workers and Celery workers
  - Route stations to nearest GPU node
- Vertical scale
  - Increase GPU memory and batch sizes per model profile
- Reliability
  - Automatic retries for transient camera/network issues
  - Health probes and restart policies for every container

## 5) Suggested SLOs
- Station ingestion availability: >= 99.9%
- Inference request success: >= 99.5%
- P95 inference latency: <= 180 ms (tunable per model)
- API availability: >= 99.9%

## 6) Recommended Deployment Topology
- Node A (GPU): ml-service + model cache + camera gateway
- Node B (CPU): Django API + Celery + Redis
- Node C (Storage/DB): PostgreSQL + object storage + backup agent
- Node D (Frontend/Proxy): Nginx + React static app

## 7) Security Controls
- Network segmentation between shop-floor and office networks
- Service-to-service auth with signed tokens
- RBAC for operators, engineers, QA managers, and admins
- Tamper-evident audit log records
- At-rest encryption for defect evidence images
