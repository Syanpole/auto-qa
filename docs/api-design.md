# REST API Design (Django REST Framework)

## Auth and Users
- POST /api/v1/auth/login
- POST /api/v1/auth/logout
- GET /api/v1/users/me
- GET /api/v1/users
- PATCH /api/v1/users/{id}

## Stations and Profiles
- GET /api/v1/stations
- POST /api/v1/stations
- PATCH /api/v1/stations/{id}
- GET /api/v1/products
- POST /api/v1/products

## Inference and Defects
- POST /api/v1/inference/realtime
  - input: station_id, product_id, image/frame metadata
  - output: verdict, defects[], latency_ms, model_version
- POST /api/v1/inference/batch
  - input: station_id optional, image list, mode options
  - output: job_id
- GET /api/v1/inference/jobs/{id}
- GET /api/v1/defects
  - filters: station, product, lot, class, date range, result
- GET /api/v1/defects/{id}
- POST /api/v1/defects/{id}/override
  - supervised disposition update with reason

## Model and Threshold Management
- GET /api/v1/models
- POST /api/v1/models/register
- POST /api/v1/models/{id}/promote
- POST /api/v1/stations/{id}/threshold
  - body: confidence_threshold, nms_threshold
- GET /api/v1/stations/{id}/threshold

## Dataset and Training
- GET /api/v1/datasets
- POST /api/v1/datasets
- POST /api/v1/training/jobs
- GET /api/v1/training/jobs
- GET /api/v1/training/jobs/{id}
- POST /api/v1/training/jobs/{id}/cancel

## Reports and Audit
- GET /api/v1/reports/shift
- GET /api/v1/reports/lot/{lot_number}
- POST /api/v1/reports/export
- GET /api/v1/audit-logs

## Health and Observability
- GET /api/v1/health
- GET /api/v1/metrics
- GET /api/v1/system/status

## Response and Error Conventions
- Standard envelope
  - success: bool
  - data: object or array
  - error: null or { code, message, details }
  - request_id: string
- Use idempotency keys for mutating operations from station gateways
- Attach model_version and threshold used in every inference response
