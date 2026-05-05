# TEST & CI/CD QUICK START

## 🚀 Quick Setup

### 1. Install Test Dependencies

```bash
# Backend tests
pip install -r backend/requirements/test.txt

# Frontend tests
npm install --save-dev @testing-library/react @testing-library/jest-dom jest jest-environment-jsdom
```

### 2. Run Tests Locally

```bash
# Backend
cd backend
pytest tests/ -v --cov=apps

# Frontend  
cd frontend
npm test

# ML Service
pytest ml-service/tests/ -v
```

### 3. View Coverage Report

```bash
# HTML report
pytest backend/tests/ --cov=apps --cov-report=html
open htmlcov/index.html
```

## 📋 What's Included

### Test Files (backend/tests/)

| File | Purpose | Tests |
|------|---------|-------|
| `conftest.py` | Shared fixtures & configuration | - |
| `test_models.py` | Django ORM models | 9 tests |
| `test_inference_api.py` | REST endpoints | 7 tests |
| `test_ml_service.py` | ML components | 12 tests |
| `test_e2e.py` | End-to-end workflows | 5 tests |
| `utils.py` | Test utilities | - |

### CI/CD Workflows (.github/workflows/)

| Workflow | Trigger | Duration |
|----------|---------|----------|
| `backend-tests.yml` | Backend changes | ~7 min |
| `frontend-tests.yml` | Frontend changes | ~4 min |
| `ml-service-tests.yml` | ML service changes | ~3 min |
| `integration-tests.yml` | All pushes/PRs | ~12 min |
| `deployment-gate.yml` | Push to main | ~5 min |

### Documentation

- **testing-guide.md**: How to write and run tests
- **ci-cd-guide.md**: Pipeline architecture and troubleshooting

## ✅ Test Coverage

```
Models:          ✅ AIModel, ModelExport, ModelDeployment
API Endpoints:   ✅ Inference, disposition, stats
ML Service:      ✅ YOLO manager, export pipeline, schemas
E2E Workflows:   ✅ Inspection, model lifecycle
```

## 🔍 Key Test Examples

### Model Tests
```python
def test_create_ai_model():
    model = AIModel.objects.create(
        model_name='ic_v1',
        version_tag='1.0.0'
    )
    assert model.model_name == 'ic_v1'
```

### API Tests
```python
def test_inference_endpoint(authenticated_client):
    response = authenticated_client.post('/api/v1/ai/infer', {...})
    assert response.status_code == 200
```

### E2E Tests
```python
def test_complete_inspection_workflow(authenticated_client):
    # Complete workflow from inspection to result
    response = authenticated_client.post('/api/v1/ai/infer', {...})
    assert response.status_code == 200
```

## 🔧 Common Commands

```bash
# Run all tests
pytest backend/tests/

# Run specific test file
pytest backend/tests/test_models.py

# Run specific test class
pytest backend/tests/test_models.py::TestAIModel

# Run with markers
pytest backend/tests/ -m unit
pytest backend/tests/ -m integration

# Run with verbose output
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=apps --cov-report=term-missing

# Run single test
pytest backend/tests/test_models.py::TestAIModel::test_create_ai_model -v
```

## 🎯 Coverage Targets

- **Overall**: >= 80%
- **Critical Paths**: >= 90%
- **Models**: >= 85%
- **API Views**: >= 80%

## ⚙️ Fixtures Available

### Pytest Fixtures (conftest.py)

```python
# Use in tests:
def test_something(authenticated_client):  
    response = authenticated_client.post('/api/v1/...')
    
def test_user_data(authenticated_user):
    assert authenticated_user.username == 'testuser'
```

### Available Fixtures
- `api_client`: DRF test client
- `authenticated_user`: Test user with password
- `authenticated_client`: Pre-authenticated DRF client

## 🚦 CI/CD Status

All workflows must pass before merge:

```
✅ Backend Tests
✅ Backend Lint  
✅ Frontend Tests
✅ Frontend Build
✅ ML Service Tests
✅ Integration Tests
```

## 📊 Database Configuration

**Test Database**: SQLite in-memory (`:memory:`)

**Advantages**:
- Fast (no I/O)
- Isolated (fresh for each test run)
- No cleanup needed

**Configuration**: `backend/config/settings/test.py`

## 🔐 Security Scanning

Tests include automatic security checks:

```
✅ Code security (bandit)
✅ Dependency audit (safety)
✅ Type checking (mypy)
```

## 📚 Documentation

Detailed guides available:

1. **testing-guide.md** - Complete testing documentation
2. **ci-cd-guide.md** - Pipeline architecture and troubleshooting
3. **yolo-integration-guide.md** - YOLO model integration
4. **yolo-deployment-guide.md** - Deployment procedures

## 🐛 Debugging Tests

```bash
# Show print statements
pytest backend/tests/ -s

# Show local variables on failure
pytest backend/tests/ -l

# Stop on first failure
pytest backend/tests/ -x

# Run failed tests only
pytest backend/tests/ --lf

# Show slowest tests
pytest backend/tests/ --durations=10
```

## ✨ Features

- ✅ **Parallel Execution**: Multi-job CI/CD pipeline
- ✅ **Database Services**: PostgreSQL for integration tests
- ✅ **Coverage Tracking**: Codecov integration
- ✅ **Docker Support**: Container build verification
- ✅ **Type Safety**: mypy type checking
- ✅ **Security**: Automated vulnerability scanning
- ✅ **Documentation**: Comprehensive guides

## 🎓 Next Steps

1. **Run locally**: `pytest backend/tests/ -v`
2. **Push to GitHub**: Workflows execute automatically
3. **Monitor**: Check Actions tab for results
4. **Review**: Check coverage reports on Codecov
5. **Deploy**: Deployment gate runs on main branch

## 📞 Support

See documentation files for:
- Test examples and patterns
- CI/CD troubleshooting
- Coverage optimization
- Performance benchmarking

---

**Test Infrastructure Ready! ✅**

All tests are configured and ready to run.

Start with: `pytest backend/tests/ -v`
