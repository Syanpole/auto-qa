# Admin Dashboard Architecture

## Dashboard Areas
- Real-time station health and throughput
- Defect history and disposition review
- Model registry and deployment panel
- Threshold management
- Model access assignment
- Live screen supervision for Super Admins
- Audit/compliance exports
- Dataset and retraining workflow management

## Role-Specific Surfaces
- Super Admin: security controls, live screens, audit exports, deployment settings
- Admin: operator supervision, thresholds, assignments, defect review, production reports
- QA Operator: inspection queue, product/model selection, own history, reject disposition actions

## Frontend Design Principles
- Prefer station-centric views with low cognitive load
- Keep live status visible at all times
- Highlight exceptions first: rejects, queue buildup, camera disconnects, and stale streams
- Use role-based navigation so users only see allowed surfaces

## Integration Points
- REST API for station, defect, model, audit, and training data
- WebSocket channel for live screen signaling and stream events
- JWT or session authentication with server-side role evaluation
