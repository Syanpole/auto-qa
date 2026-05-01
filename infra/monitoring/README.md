# Monitoring and Alerting Baseline

## Metrics to Collect
- API request rate, errors, latency (p50/p95/p99)
- Celery queue depth, task duration, task failure rate
- Inference latency per station/model and FPS
- GPU utilization, temperature, memory
- Defect rates by class and station
- False reject and false accept trend

## Alerts
- Camera stream disconnected > 30 seconds
- Inference p95 latency > configured threshold for 10 minutes
- Queue backlog above safety threshold
- Postgres disk usage > 80%
- Daily KPI drift beyond guardrails

## Recommended Stack
- Prometheus + Grafana
- Loki/ELK for logs
- Alertmanager with email/SMS integration
