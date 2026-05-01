# Security and RBAC Design

## Roles

### Super Admin
- Full system administration
- Manage users, groups, permissions, model access, deployment settings, and live QA screens
- Export audit logs and compliance reports
- Trigger retraining and promote models

### Admin
- Supervise QA operators
- Assign station/model access
- Manage station workflows and production reports
- Review rejected products

### QA Operator
- Inspect assigned products at assigned stations
- Run approved models only
- View own inspection history
- Acknowledge pass/reject outcomes
- Select rework or waste for rejects

## Enforcement Pattern
- Django Groups define the role boundary.
- Custom model permissions gate privileged actions.
- Viewset permissions enforce API-level checks.
- ModelAccess records gate model loading and inference.
- Audit logs capture every privileged action.

## Operational Rules
- Super Admin is the only role that can view live QA screens.
- Admin can assign model access but cannot change security controls.
- Operators can only query the models and stations they are assigned.
- Failed login attempts, permission changes, threshold changes, and inference overrides are immutable audit events.
