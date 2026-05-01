# Team Pacific Corporation AUTO QA System (teamglac)

Enterprise-grade AI-powered Automatic Quality Assurance system for semiconductor IC defect detection.

## Objective
Build a production-ready AUTO QA platform for real-time IC defect detection (scratches, cracks, chips, surface damage, mesa-type die defects) using ESMD-YOLOv26n and RT-DETR with multi-station inference, retraining, traceability, and 24/7 manufacturing reliability.

## Key Capabilities
- Real-time industrial camera ingest and defect detection
- Multi-inference orchestration across QA stations
- Model registry, dataset versioning, and self-training workflows
- On-prem inference with optional cloud training via Ultralytics HUB
- Web dashboard for live station status and defect analytics
- Confidence threshold controls (default: 0.85)
- Full audit trail, defect history, and report exports

## Recommended High-Level Stack
- Backend: Django, Django REST Framework, PostgreSQL, Celery, Redis
- AI/ML: PyTorch, Ultralytics YOLO, RT-DETR, OpenCV, ONNX Runtime, TensorRT
- Frontend: React, Tailwind CSS, ECharts
- Deployment: Docker, Ubuntu LTS, NVIDIA GPU runtime, Nginx reverse proxy

## Project Structure
- backend/: Django API, domain services, audit, training workflows
- ml-service/: Inference microservice (YOLO/RT-DETR abstraction)
- frontend/: React monitoring dashboard
- docs/: Architecture, schema, API and deployment design
- deploy/: Container and infrastructure deployment assets
- infra/: Monitoring and observability templates

## KPI Targets
- Detection accuracy: >95%
- False reject rate: <3%
- False accept rate: <2%
- Throughput: 3-5x faster than manual inspection
- Rework cost reduction: 30-50%

## Quick Start (Design Scaffold)
1. Review docs/architecture.md and docs/deployment-workflow.md.
2. Configure environment variables from .env.example.
3. Build and run containers with docker compose.
4. Connect camera gateways and validate inference latency/stability.
5. Start pilot rollout at one QA line before full deployment.

## Security and Reliability Notes
- Role-based access and API token controls are mandatory.
- Enforce TLS for dashboard and API communications.
- Keep inference on-prem for production; cloud training is optional.
- Use RAID-backed storage for image evidence and training artifacts.
- Add active monitoring and alerting for model drift and station downtime.
