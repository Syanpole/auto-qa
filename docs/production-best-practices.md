# Production Best Practices

## Architecture
- Keep inference and control-plane services separated.
- Use immutable image tags and versioned model artifacts.
- Design station APIs as idempotent.

## Model Governance
- Record dataset lineage for every trained model.
- Validate on holdout sets and real production samples.
- Use canary or shadow rollout before full promotion.

## Security
- Rotate credentials and API tokens regularly.
- Restrict model upload and promotion actions by role.
- Encrypt sensitive defect evidence at rest.

## Reliability
- Apply graceful degradation when camera feeds fail.
- Add retry with circuit breakers for service dependencies.
- Maintain tested rollback playbooks for model and app releases.

## Data and Compliance
- Keep immutable audit logs for threshold/model changes.
- Define retention and purge policy for image evidence.
- Review access logs routinely.
