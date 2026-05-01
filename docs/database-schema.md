# Database Schema Recommendation (PostgreSQL)

## Core Tables

### users
- id (uuid, pk)
- username (varchar, unique)
- email (varchar, unique)
- password_hash (varchar)
- role (varchar) -> operator | qa_engineer | supervisor | admin
- is_active (bool)
- created_at (timestamp)
- updated_at (timestamp)

### qa_station
- id (uuid, pk)
- station_code (varchar, unique)
- station_name (varchar)
- line_name (varchar)
- camera_endpoint (varchar)
- is_enabled (bool)
- created_at (timestamp)

### product_profile
- id (uuid, pk)
- product_code (varchar, unique)
- product_name (varchar)
- package_type (varchar)
- notes (text)
- created_at (timestamp)

### model_registry
- id (uuid, pk)
- model_name (varchar)
- model_family (varchar) -> esmd_yolov26n | rtdetr
- version_tag (varchar)
- framework (varchar)
- weights_uri (varchar)
- onnx_uri (varchar, nullable)
- tensorrt_uri (varchar, nullable)
- status (varchar) -> draft | validated | production | archived
- metrics_json (jsonb)
- trained_at (timestamp)
- promoted_at (timestamp, nullable)

### station_model_assignment
- id (uuid, pk)
- station_id (uuid, fk qa_station)
- product_id (uuid, fk product_profile)
- model_id (uuid, fk model_registry)
- confidence_threshold (numeric(4,3), default 0.850)
- nms_threshold (numeric(4,3), default 0.500)
- is_active (bool)
- updated_by (uuid, fk users)
- updated_at (timestamp)

### defect_event
- id (uuid, pk)
- event_ts (timestamp)
- station_id (uuid, fk qa_station)
- product_id (uuid, fk product_profile)
- lot_number (varchar)
- wafer_or_strip_id (varchar)
- unit_serial (varchar)
- defect_class (varchar)
- confidence (numeric(5,4))
- severity (varchar)
- bbox_json (jsonb)
- result (varchar) -> pass | fail | review
- model_id (uuid, fk model_registry)
- image_uri (varchar)
- overlay_uri (varchar)
- raw_meta_json (jsonb)

### inference_job
- id (uuid, pk)
- mode (varchar) -> realtime | batch
- station_id (uuid, fk qa_station, nullable)
- total_images (int)
- started_at (timestamp)
- finished_at (timestamp, nullable)
- status (varchar) -> queued | running | completed | failed
- error_message (text, nullable)

### dataset_version
- id (uuid, pk)
- dataset_name (varchar)
- version_tag (varchar)
- source_type (varchar) -> production_capture | imported | mixed
- class_distribution_json (jsonb)
- storage_uri (varchar)
- created_by (uuid, fk users)
- created_at (timestamp)

### training_job
- id (uuid, pk)
- dataset_id (uuid, fk dataset_version)
- base_model_id (uuid, fk model_registry)
- output_model_id (uuid, fk model_registry, nullable)
- params_json (jsonb)
- status (varchar) -> queued | running | completed | failed
- started_at (timestamp)
- finished_at (timestamp, nullable)
- logs_uri (varchar, nullable)

### audit_log
- id (bigserial, pk)
- actor_id (uuid, fk users, nullable)
- action (varchar)
- resource_type (varchar)
- resource_id (uuid, nullable)
- request_id (varchar)
- details_json (jsonb)
- created_at (timestamp)

## Indexing Strategy
- defect_event(station_id, event_ts desc)
- defect_event(product_id, defect_class, event_ts desc)
- defect_event(result, event_ts desc)
- model_registry(status, promoted_at desc)
- training_job(status, started_at desc)
- audit_log(created_at desc)

## Retention Policy
- Hot data (postgres): 6-12 months defect metadata
- Cold archive (object storage): images, overlays, old training logs
- Weekly partitioning for defect_event recommended at high throughput
