# CI/CD Pipeline Documentation

## Overview

The AUTO QA system uses GitHub Actions for continuous integration and continuous deployment. The pipeline ensures code quality, test coverage, security, and deployment readiness.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Code Push / Pull Request                    │
└─────────────────────────────────────────────────────────────┘
                         ↓
        ┌────────────────┬────────────────┬──────────────┐
        ↓                ↓                ↓              ↓
  ┌──────────────┐ ┌───────────┐ ┌──────────────┐ ┌─────────┐
  │ Backend      │ │ Frontend  │ │ ML Service   │ │Integration
  │ Tests        │ │ Tests     │ │ Tests        │ │Tests
  └──────────────┘ └───────────┘ └──────────────┘ └─────────┘
        ↓                ↓                ↓              ↓
  ┌──────────────┐ ┌───────────┐ ┌──────────────┐ ┌─────────┐
  │ Lint & QA    │ │ Build     │ │ Lint & QA    │ │Docker
  │ Code Quality │ │ Check     │ │              │ │Build
  └──────────────┘ └───────────┘ └──────────────┘ └─────────┘
        ↓                ↓                ↓              ↓
        └────────────────┴────────────────┴──────────────┘
                         ↓
              ┌──────────────────────┐
              │  All Checks Pass?    │
              └──────────────────────┘
              ↓ Yes          ↓ No
         ┌─────────┐      ┌──────────────┐
         │ Approve │      │ Block Merge  │
         │  Merge  │      │ (Require Fix)│
         └─────────┘      └──────────────┘
              ↓
    ┌────────────────────┐
    │ Merge to main      │
    └────────────────────┘
              ↓
    ┌────────────────────┐
    │ Deployment Gate    │
    │ (Pre-deployment)   │
    └────────────────────┘
              ↓
    ┌────────────────────┐
    │ Deploy to          │
    │ Staging/Prod       │
    └────────────────────┘
```

## Workflows

### 1. Backend Tests (`backend-tests.yml`)

**Trigger**: Push/PR to main/develop with backend changes

**Jobs**:
- **test**: Run unit tests with PostgreSQL service
  - Database: PostgreSQL 15
  - Python: 3.12
  - Coverage: >= 80%
  - Tools: pytest, pytest-cov, pytest-django

- **lint**: Code quality checks
  - Black (formatting)
  - isort (import sorting)
  - flake8 (PEP8 compliance)
  - mypy (type checking)

- **security**: Security scanning
  - bandit (Python security)
  - safety (dependency audit)

**Duration**: ~5-10 minutes

### 2. Frontend Tests (`frontend-tests.yml`)

**Trigger**: Push/PR to main/develop with frontend changes

**Jobs**:
- **test**: Run React component tests
  - Node: 18.x
  - Coverage report upload
  
- **build**: Verify production build
  - Check build artifacts
  - Upload to workflow artifacts

- **lint**: Code quality and type checking
  - ESLint
  - Type checking (TSC)

**Duration**: ~3-5 minutes

### 3. ML Service Tests (`ml-service-tests.yml`)

**Trigger**: Push/PR to main/develop with ml-service changes

**Jobs**:
- **test**: Unit tests for ML service
  - Python: 3.12
  - Coverage: >= 80%
  - Tools: pytest, pytest-cov

- **lint**: Code quality
  - Black, isort, flake8

**Duration**: ~2-3 minutes

### 4. Integration Tests (`integration-tests.yml`)

**Trigger**: All pushes and PRs

**Jobs**:
- **integration**: Full integration test suite
  - PostgreSQL service
  - Database migration verification
  - API integration tests
  - Coverage upload

- **docker-build**: Docker image builds
  - Backend image (caching enabled)
  - ML service image
  - Frontend image

**Duration**: ~10-15 minutes

### 5. Deployment Gate (`deployment-gate.yml`)

**Trigger**: Push to main branch

**Prerequisites**:
- All previous tests pass
- Coverage >= 80%
- No linting errors
- Successful build

**Checks**:
- Final code quality verification
- Security audit
- Build verification
- Deployment readiness summary

**Duration**: ~5 minutes

## Status Checks

### Required Status Checks

All of the following must pass for PR merge:

```
✅ Backend Tests
✅ Backend Lint
✅ Frontend Tests
✅ Frontend Build
✅ ML Service Tests
✅ Integration Tests
```

### Optional Status Checks

```
⚪ Security Scan (advisory)
⚪ Performance Benchmark
```

## Configuration

### Branch Protection Rules

For `main` branch:

```yaml
Require status checks to pass before merging:
  - backend-tests / test
  - backend-tests / lint
  - frontend-tests / test
  - frontend-tests / build
  - ml-service-tests / test
  - integration-tests / integration

Require code review:
  - Minimum 1 approving review
  - Dismiss stale reviews
  - Require review from code owners

Require branches to be up to date:
  - Yes

Require status checks for administrators:
  - Yes
```

### Repository Secrets

Add these secrets in GitHub repository settings:

```
REGISTRY_USERNAME    # Docker registry username
REGISTRY_PASSWORD    # Docker registry password
DEPLOYMENT_TOKEN     # API token for deployment
DATABASE_URL         # Test database URL
```

## Failure Handling

### Test Failure

1. Pipeline fails and blocks merge
2. PR author receives notification
3. Author must fix and push new commit
4. Pipeline re-runs automatically

### Coverage Failure

If coverage < 80%:

1. Coverage report generated
2. Detailed report linked in PR
3. Author must add tests
4. Pipeline re-runs

### Security Issues

If bandit finds issues:

1. Security report generated
2. Issues flagged in PR
3. Author must fix or approve
4. Requires explicit override

## Performance Optimization

### Caching

```yaml
- pip cache: ~/.cache/pip/
- npm cache: ~/.npm/
- Docker layer caching: registry cache
```

### Parallel Execution

- Backend, Frontend, ML Service tests run in parallel
- Reduces total pipeline time from ~15min to ~10min

### Conditional Runs

- Backend tests only run on backend changes
- Frontend tests only run on frontend changes
- Integration tests run on all changes

## Monitoring

### Workflow Status

View workflow status at:
```
https://github.com/YOUR_ORG/auto-qa/actions
```

### Coverage Tracking

Coverage reports uploaded to:
```
Codecov: https://codecov.io/gh/YOUR_ORG/auto-qa
```

### Deployment History

View deployments at:
```
https://github.com/YOUR_ORG/auto-qa/deployments
```

## Troubleshooting

### Pipeline Fails

1. **Check logs**: Click on failed job to view logs
2. **Identify error**: Look for red X and error message
3. **Fix locally**: Reproduce and fix on local machine
4. **Push fix**: Commit and push to re-trigger pipeline

### Cache Issues

```bash
# Clear cache if tests fail mysteriously
# Settings → Actions → General → Cache → Clear all caches
```

### Dependencies Out of Date

```bash
# Locally update dependencies
pip install --upgrade -r requirements.txt
npm update

# Commit and push to test
```

## Deployment Checklist

Before deploying to production:

- [ ] All tests passing on main
- [ ] Coverage >= 80%
- [ ] No security warnings
- [ ] Build artifacts present
- [ ] Database migrations tested
- [ ] Performance benchmarks acceptable
- [ ] Documentation updated
- [ ] Version bumped

## Best Practices

1. **Commit message**: Use descriptive messages
   ```
   feat: Add real-time detection UI
   ```

2. **Small PRs**: Keep changes focused and reviewable

3. **Test locally**: Run tests before pushing
   ```bash
   pytest backend/tests/
   npm test
   ```

4. **Monitor CI**: Watch pipeline during PR review

5. **Review logs**: Check detailed logs for warnings

6. **Update docs**: Keep docs in sync with code

## Debugging CI Failures

### Access logs

```bash
# Download artifact from workflow
# Go to Actions → Workflow Run → Artifacts
```

### Reproduce locally

```bash
# Use same Python/Node version as CI
python --version  # Should be 3.12
node --version    # Should be 18.x

# Run exact same command as CI
pytest backend/tests/ --cov=apps
```

### Check environment variables

```bash
# CI sets different variables than local
# Check .github/workflows/*.yml for env vars
```

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [PyTest](https://docs.pytest.org/)
- [Jest Testing](https://jestjs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Last Updated**: May 1, 2026
**Maintained By**: Team Pacific Corporation
