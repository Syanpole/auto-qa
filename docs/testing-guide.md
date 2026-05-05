# Testing Documentation

## Running Tests

### Backend Tests

```bash
# Run all backend tests
pytest backend/tests/

# Run with coverage
pytest backend/tests/ --cov=apps --cov-report=html

# Run specific test file
pytest backend/tests/test_models.py

# Run specific test class
pytest backend/tests/test_models.py::TestAIModel

# Run specific test
pytest backend/tests/test_models.py::TestAIModel::test_create_ai_model

# Run with verbose output
pytest backend/tests/ -v

# Run with markers
pytest backend/tests/ -m unit
pytest backend/tests/ -m integration
```

### Frontend Tests

```bash
# Run all frontend tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- test_name.test.tsx

# Run in watch mode
npm test -- --watch
```

### ML Service Tests

```bash
# Run ML service tests
pytest ml-service/tests/

# Run with coverage
pytest ml-service/tests/ --cov=app
```

## Test Structure

### Backend Tests (`backend/tests/`)

- **conftest.py**: Pytest configuration and shared fixtures
- **test_models.py**: Django model tests (AIModel, ModelExport, ModelDeployment)
- **test_inference_api.py**: REST API endpoint tests
- **test_ml_service.py**: ML service component tests
- **test_e2e.py**: End-to-end workflow tests
- **utils.py**: Test utilities and helpers

### Test Markers

```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.e2e           # End-to-end tests
@pytest.mark.slow          # Slow running tests
```

## Fixtures

### Common Fixtures (conftest.py)

```python
api_client              # DRF test client
authenticated_user      # Test user
authenticated_client    # Authenticated API client
```

### Model Fixtures

```python
test_image_base64      # Base64 encoded test image
test_station_and_product  # QA station + product
```

## Test Coverage

### Target Coverage

- Overall: >= 80%
- Critical paths (inference, deployment): >= 90%
- Models: >= 85%
- API views: >= 80%

### View Coverage Report

```bash
# Generate HTML coverage report
pytest backend/tests/ --cov=apps --cov-report=html

# Open report
open htmlcov/index.html
```

## CI/CD Workflows

### Backend Tests (`.github/workflows/backend-tests.yml`)

Runs on push/PR to main/develop:
- Unit tests
- Code linting (flake8, black, isort)
- Type checking (mypy)
- Security checks (bandit)

### Frontend Tests (`.github/workflows/frontend-tests.yml`)

Runs on push/PR to main/develop:
- Unit & component tests
- Build verification
- Linting
- Type checking

### Integration Tests (`.github/workflows/integration-tests.yml`)

Runs on all pushes/PRs:
- Full integration tests
- Docker build verification
- Database schema validation

### Deployment Gate (`.github/workflows/deployment-gate.yml`)

Runs before production deployment:
- All tests must pass
- Code quality checks
- Security audit
- Build verification

## Writing Tests

### Unit Test Example

```python
@pytest.mark.django_db
class TestAIModel:
    def test_create_model(self):
        model = AIModel.objects.create(
            model_name='ic_v1',
            version_tag='1.0.0',
            model_family='yolov8'
        )
        assert model.model_name == 'ic_v1'
```

### API Test Example

```python
def test_inference_endpoint(authenticated_client):
    response = authenticated_client.post(
        '/api/v1/ai/infer',
        {'image_base64': 'test', 'station_id': 'A', 'product_id': 'IC_001'}
    )
    assert response.status_code in [200, 400]
```

### E2E Test Example

```python
def test_complete_workflow(authenticated_client):
    # Setup
    station = QAStation.objects.create(station_code='A')
    
    # Act
    response = authenticated_client.post('/api/v1/ai/infer', {...})
    
    # Assert
    assert response.status_code == 200
```

## Best Practices

1. **Use fixtures** for common setup (users, models, etc)
2. **Mark tests** appropriately (@pytest.mark.unit, etc)
3. **Use descriptive names** (test_create_ai_model_successfully)
4. **Keep tests focused** (one assertion per test when possible)
5. **Use factories** for complex test data
6. **Mock external services** (ML service, third-party APIs)
7. **Test edge cases** (invalid input, missing fields, etc)
8. **Maintain test database** clean between tests

## Troubleshooting

### Tests fail with "Table doesn't exist"

```bash
# Run migrations first
python manage.py migrate --settings=config.settings.test
```

### Import errors in tests

```bash
# Ensure backend is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
```

### Coverage reports not generated

```bash
# Install coverage tool
pip install coverage pytest-cov
```

### Database lock errors

```bash
# Use SQLite in-memory database for tests (default)
# Or disable transactional tests for PostgreSQL
```

## Continuous Integration

### Status Checks

All PRs must pass:
- ✅ Backend Tests
- ✅ Frontend Tests  
- ✅ ML Service Tests
- ✅ Integration Tests
- ✅ Code Quality (linting)
- ✅ Type Checking
- ✅ Security Audit

### Deployment Requirements

To deploy to production:
- All main branch tests passing
- Coverage >= 80%
- No critical security issues
- Build artifacts valid
- Database migrations tested

## Performance Benchmarks

### Test Execution Time

- Unit tests: < 30 seconds
- Integration tests: < 2 minutes
- Full suite: < 5 minutes

### Code Quality Metrics

- Cyclomatic complexity: < 10
- Duplication: < 5%
- Maintainability index: > 70

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Coverage.py](https://coverage.readthedocs.io/)
