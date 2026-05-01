# Deployment Workflow (Enterprise On-Prem)

## 1) Infrastructure Baseline
- Ubuntu Server 22.04 or 24.04 LTS
- NVIDIA RTX 4090 with tested CUDA and cuDNN versions
- RAID-backed storage for image evidence and backups
- Isolated VLAN for production QA network

## 2) Build and Validation Stages
1. CI build stage
   - Build backend, frontend, and ml-service images
   - Run static checks and unit tests
2. Integration stage
   - Spin up compose stack in staging
   - Run API and inference smoke tests
3. Performance stage
   - Validate latency and throughput against station load
4. Security stage
   - Container vulnerability scan and dependency checks
5. Release stage
   - Tag image versions and deploy with immutable tags

## 3) Runtime Deployment
- Nginx reverse proxy terminates TLS and routes services
- Django API + Celery workers run in replicated CPU containers
- ml-service runs on GPU nodes with NVIDIA container runtime
- PostgreSQL uses persistent volumes and scheduled backups
- Redis runs as broker/cache with persistence enabled

## 4) Model Lifecycle in Production
- Register new model artifact and metadata
- Run shadow validation against production samples
- Promote model per station/product profile
- Monitor drift and KPI regressions continuously
- Roll back immediately if false reject/accept exceeds guardrails

## 5) Backup and Disaster Recovery
- PostgreSQL: nightly full backup + WAL archive
- Object storage: versioning and replication
- Config and secrets: encrypted backup copy
- Recovery drills: quarterly restore validation

## 6) 24/7 Operations Checklist
- Alerting on camera disconnect, queue backlog, GPU thermal, API errors
- On-call runbook for station failover and model rollback
- Daily KPI review by line and defect type
- Weekly threshold calibration review
