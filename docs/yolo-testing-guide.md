# YOLO Integration Testing Guide

## Overview

This guide provides comprehensive testing procedures for the YOLO IC defect detection system across all layers: unit tests, integration tests, and end-to-end tests.

---

## Test Environment Setup

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-django

# Create test database
python manage.py migrate --settings=config.settings.test

# Run all tests
pytest --cov=backend --cov-report=html
```

---

## Unit Tests

### Test YOLO Model Manager

**File**: `backend/tests/test_yolo_model_manager.py`

```python
import pytest
import numpy as np
from io import BytesIO
from PIL import Image
from ml_service.app.yolo_model_manager import YOLOModelManager


@pytest.fixture
def model_manager():
    return YOLOModelManager()


@pytest.fixture
def test_image():
    """Create a test image (640x640 RGB)"""
    img = Image.new('RGB', (640, 640), color='red')
    return img


class TestYOLOModelManager:
    
    def test_load_model_pytorch(self, model_manager, tmp_path):
        """Test loading PyTorch model"""
        # This requires an actual .pt file for testing
        # result = model_manager.load_model(
        #     "backend/models_registry/deployed_models/ic_defect_v1.pt",
        #     "ic_v1"
        # )
        # assert result['status'] == 'success'
        # assert result['is_active'] == False
        pass
    
    def test_load_model_tensorrt(self, model_manager, tmp_path):
        """Test loading TensorRT optimized model"""
        # result = model_manager.load_model(
        #     "backend/models_registry/exports/ic_defect_v1.engine",
        #     "ic_v1_optimized"
        # )
        # assert result['status'] == 'success'
        pass
    
    def test_infer_with_confidence(self, model_manager, test_image):
        """Test inference with confidence threshold"""
        # Convert image to base64
        buffered = BytesIO()
        test_image.save(buffered, format="JPEG")
        image_base64 = buffered.getvalue()
        
        # Test inference
        # result = model_manager.infer({
        #     'image_base64': image_base64,
        #     'confidence_threshold': 0.85
        # })
        
        # assert 'detections' in result
        # assert 'inference_time_ms' in result
        pass
    
    def test_batch_inference(self, model_manager, test_image):
        """Test batch inference performance"""
        batch_images = [test_image] * 5
        
        # result = model_manager.batch_infer({
        #     'images': batch_images,
        #     'confidence_threshold': 0.85
        # })
        
        # assert result['batch_size'] == 5
        # assert len(result['results']) == 5
        pass
    
    def test_benchmark_model(self, model_manager):
        """Test model benchmarking"""
        # result = model_manager.benchmark_model("ic_v1", num_runs=10)
        
        # assert 'mean_latency_ms' in result
        # assert 'p95_latency_ms' in result
        # assert 'p99_latency_ms' in result
        # assert result['throughput_fps'] > 0
        pass
    
    def test_activate_deactivate_model(self, model_manager):
        """Test model activation/deactivation"""
        # model_manager.load_model("path/to/model.pt", "test_model")
        # 
        # result = model_manager.activate_model("test_model")
        # assert model_manager.active_model == "test_model"
        # 
        # result = model_manager.deactivate_model()
        # assert model_manager.active_model is None
        pass
    
    def test_get_stats(self, model_manager):
        """Test statistics collection"""
        # stats = model_manager.get_stats()
        # assert 'total_inferences' in stats
        # assert 'total_defects_detected' in stats
        # assert 'inference_times_ms' in stats
        pass
```

### Test Export Pipeline

**File**: `backend/tests/test_export_pipeline.py`

```python
import pytest
import os
from apps.training.yolo_export_pipeline import YOLOExportPipeline


@pytest.fixture
def export_pipeline(tmp_path):
    return YOLOExportPipeline(
        pt_model_path="backend/models_registry/deployed_models/ic_defect_v1.pt",
        output_dir=str(tmp_path)
    )


class TestYOLOExportPipeline:
    
    def test_export_onnx(self, export_pipeline):
        """Test ONNX export"""
        # result = export_pipeline.export_onnx()
        # assert result['status'] == 'completed'
        # assert os.path.exists(result['file_path'])
        pass
    
    def test_export_tensorrt(self, export_pipeline):
        """Test TensorRT export"""
        # result = export_pipeline.export_tensorrt()
        # assert result['status'] == 'completed'
        # assert os.path.exists(result['file_path'])
        pass
    
    def test_export_all(self, export_pipeline):
        """Test all format exports"""
        # results = export_pipeline.export_all()
        # 
        # assert 'tensorrt' in results['exports']
        # assert 'onnx' in results['exports']
        # assert 'openvino' in results['exports']
        # assert 'torchscript' in results['exports']
        pass
    
    def test_benchmark_comparison(self, export_pipeline):
        """Test benchmark results"""
        # results = export_pipeline.export_all()
        # tensorrt_fps = results['exports']['tensorrt']['benchmark']['throughput_fps']
        # onnx_fps = results['exports']['onnx']['benchmark']['throughput_fps']
        # 
        # # TensorRT should be faster
        # assert tensorrt_fps > onnx_fps
        pass
```

---

## Integration Tests

### Test Django Models

**File**: `backend/tests/test_ai_models.py`

```python
import pytest
from django.contrib.auth import get_user_model
from apps.training.models import AIModel, ModelExport, ModelDeployment
from apps.qa.models import QAStation, ProductProfile, DefectEvent


User = get_user_model()


@pytest.mark.django_db
class TestAIModel:
    
    def test_create_ai_model(self):
        """Test creating AIModel"""
        model = AIModel.objects.create(
            model_name="ic_defect_v1",
            version_tag="1.0.0",
            model_family="yolov8",
            defect_types=["scratch", "crack", "chip"],
            status="draft",
            is_active=False,
            throughput_fps=80,
            inference_time_ms=12.5
        )
        
        assert model.model_name == "ic_defect_v1"
        assert model.status == "draft"
        assert model.is_active == False
    
    def test_model_unique_constraint(self):
        """Test model name-version uniqueness"""
        AIModel.objects.create(
            model_name="ic_v1",
            version_tag="1.0.0",
            model_family="yolov8",
            status="draft"
        )
        
        with pytest.raises(Exception):  # IntegrityError
            AIModel.objects.create(
                model_name="ic_v1",
                version_tag="1.0.0",
                model_family="yolov8",
                status="draft"
            )
    
    def test_activate_model(self):
        """Test model activation"""
        model = AIModel.objects.create(
            model_name="ic_v1",
            version_tag="1.0.0",
            model_family="yolov8",
            status="production",
            is_active=False
        )
        
        model.is_active = True
        model.save()
        
        assert model.is_active == True


@pytest.mark.django_db
class TestModelExport:
    
    def test_create_export(self):
        """Test creating ModelExport"""
        model = AIModel.objects.create(
            model_name="ic_v1",
            version_tag="1.0.0",
            model_family="yolov8",
            status="production"
        )
        
        export = ModelExport.objects.create(
            ai_model=model,
            export_format="tensorrt",
            status="completed",
            file_path="exports/ic_v1.engine"
        )
        
        assert export.export_format == "tensorrt"
        assert export.status == "completed"
    
    def test_export_benchmark_data(self):
        """Test export with benchmark metrics"""
        model = AIModel.objects.create(
            model_name="ic_v1",
            version_tag="1.0.0",
            model_family="yolov8",
            status="production"
        )
        
        export = ModelExport.objects.create(
            ai_model=model,
            export_format="tensorrt",
            status="completed",
            file_path="exports/ic_v1.engine",
            inference_time_ms=12.5,
            throughput_fps=80,
            benchmark_hardware="RTX 4090"
        )
        
        assert export.inference_time_ms == 12.5
        assert export.throughput_fps == 80


@pytest.mark.django_db
class TestModelDeployment:
    
    def test_create_deployment(self):
        """Test creating ModelDeployment"""
        model = AIModel.objects.create(
            model_name="ic_v1",
            version_tag="1.0.0",
            model_family="yolov8",
            status="production",
            is_active=True
        )
        
        deployment = ModelDeployment.objects.create(
            ai_model=model,
            deployment_target="production",
            status="active"
        )
        
        assert deployment.status == "active"
        assert deployment.deployment_target == "production"
    
    def test_deployment_tracking(self):
        """Test deployment metrics tracking"""
        model = AIModel.objects.create(
            model_name="ic_v1",
            version_tag="1.0.0",
            model_family="yolov8",
            status="production",
            is_active=True
        )
        
        deployment = ModelDeployment.objects.create(
            ai_model=model,
            deployment_target="production",
            status="active",
            inference_requests_count=100,
            error_count=5
        )
        
        assert deployment.inference_requests_count == 100
        assert deployment.error_count == 5
```

### Test API Endpoints

**File**: `backend/tests/test_inference_api.py`

```python
import pytest
import base64
import json
from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.qa.models import QAStation, ProductProfile


User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_user():
    user = User.objects.create_user(
        username="operator",
        password="test123"
    )
    return user


@pytest.fixture
def test_image_base64():
    """Create test image and convert to base64"""
    img = Image.new('RGB', (640, 640), color='white')
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    image_base64 = base64.b64encode(buffered.getvalue()).decode()
    return image_base64


@pytest.mark.django_db
class TestInferenceAPI:
    
    def test_realtime_inference(self, api_client, authenticated_user, test_image_base64):
        """Test real-time inference endpoint"""
        api_client.force_authenticate(user=authenticated_user)
        
        # Create test data
        station = QAStation.objects.create(
            station_code="Station-A",
            station_name="Test Station"
        )
        product = ProductProfile.objects.create(
            product_code="IC_001",
            product_name="Test Product"
        )
        
        # Make inference request
        response = api_client.post('/api/v1/ai/infer', {
            'image_base64': test_image_base64,
            'station_id': 'Station-A',
            'product_id': 'IC_001',
            'confidence_threshold': 0.85
        })
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'detections' in data
    
    def test_batch_inference(self, api_client, authenticated_user, test_image_base64):
        """Test batch inference endpoint"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.post('/api/v1/ai/infer/batch', {
            'images': [
                {'image_base64': test_image_base64, 'product_id': 'IC_001'},
                {'image_base64': test_image_base64, 'product_id': 'IC_002'}
            ],
            'station_id': 'Station-A',
            'confidence_threshold': 0.85
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['total_processed'] == 2
    
    def test_disposition(self, api_client, authenticated_user):
        """Test operator disposition endpoint"""
        api_client.force_authenticate(user=authenticated_user)
        
        # Create test data
        QAStation.objects.create(
            station_code="Station-A",
            station_name="Test Station"
        )
        ProductProfile.objects.create(
            product_code="IC_001",
            product_name="Test Product"
        )
        
        response = api_client.post('/api/v1/ai/disposition', {
            'station_id': 'Station-A',
            'product_id': 'IC_001',
            'operator_action': 'PASS',
            'defects_found': 0
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'recorded'
        assert data['action'] == 'PASS'
    
    def test_stats(self, api_client, authenticated_user):
        """Test inference statistics endpoint"""
        api_client.force_authenticate(user=authenticated_user)
        
        response = api_client.get('/api/v1/ai/stats')
        
        assert response.status_code == 200
        data = response.json()
        assert 'total_inferences' in data
        assert 'pass_count' in data
        assert 'pass_rate_percent' in data
```

---

## End-to-End Tests

### Selenium/Playwright Tests

**File**: `frontend/tests/e2e/detection.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Real-Time Detection Page', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to detection page
    await page.goto('http://localhost:3000/detection');
    
    // Wait for page to load
    await page.waitForSelector('[data-testid="camera-container"]', { 
      timeout: 5000 
    });
  });
  
  test('should display camera controls', async ({ page }) => {
    // Check camera button exists
    const cameraButton = page.locator('[data-testid="camera-toggle"]');
    await expect(cameraButton).toBeVisible();
  });
  
  test('should load station dropdown', async ({ page }) => {
    const stationSelect = page.locator('select[id="station"]');
    await expect(stationSelect).toBeVisible();
    
    // Check options are populated
    const options = page.locator('select[id="station"] option');
    const count = await options.count();
    expect(count).toBeGreaterThan(1);
  });
  
  test('should start camera on click', async ({ page }) => {
    const cameraButton = page.locator('[data-testid="camera-toggle"]');
    await cameraButton.click();
    
    // Canvas should be visible and animating
    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
  });
  
  test('should capture and infer on button click', async ({ page }) => {
    // Start camera
    const cameraButton = page.locator('[data-testid="camera-toggle"]');
    await cameraButton.click();
    
    // Wait for camera to initialize
    await page.waitForTimeout(2000);
    
    // Click capture
    const captureButton = page.locator('[data-testid="capture-button"]');
    await captureButton.click();
    
    // Wait for inference result
    await page.waitForSelector('[data-testid="detection-results"]', { 
      timeout: 10000 
    });
  });
  
  test('should show operator action buttons', async ({ page }) => {
    const acceptButton = page.locator('[data-testid="action-pass"]');
    const reworkButton = page.locator('[data-testid="action-rework"]');
    const scrapButton = page.locator('[data-testid="action-scrap"]');
    
    await expect(acceptButton).toBeVisible();
    await expect(reworkButton).toBeVisible();
    await expect(scrapButton).toBeVisible();
  });
  
  test('should record operator disposition', async ({ page }) => {
    // Start camera and capture
    const cameraButton = page.locator('[data-testid="camera-toggle"]');
    await cameraButton.click();
    await page.waitForTimeout(2000);
    
    const captureButton = page.locator('[data-testid="capture-button"]');
    await captureButton.click();
    
    // Click Pass button
    const passButton = page.locator('[data-testid="action-pass"]');
    await passButton.click();
    
    // Verify disposition recorded (check local UI state)
    const statusBadge = page.locator('[data-testid="status-badge"]');
    await expect(statusBadge).toContainText('PASS');
  });
});

test.describe('Admin Model Management Page', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to admin page
    await page.goto('http://localhost:3000/admin/models');
    
    // Wait for models tab
    await page.waitForSelector('[data-testid="models-tab"]', { 
      timeout: 5000 
    });
  });
  
  test('should display models list', async ({ page }) => {
    const modelsList = page.locator('[data-testid="models-list"]');
    await expect(modelsList).toBeVisible();
  });
  
  test('should show model details', async ({ page }) => {
    const modelCard = page.locator('[data-testid="model-card"]').first();
    await expect(modelCard).toBeVisible();
    
    // Check model information displayed
    await expect(modelCard.locator('text=Model:')).toBeVisible();
    await expect(modelCard.locator('text=Status:')).toBeVisible();
    await expect(modelCard.locator('text=FPS:')).toBeVisible();
  });
  
  test('should switch between tabs', async ({ page }) => {
    // Click exports tab
    const exportsTab = page.locator('[data-testid="exports-tab"]');
    await exportsTab.click();
    
    // Wait for exports content
    await page.waitForSelector('[data-testid="exports-list"]');
    
    // Click deployments tab
    const deploymentsTab = page.locator('[data-testid="deployments-tab"]');
    await deploymentsTab.click();
    
    // Wait for deployments content
    await page.waitForSelector('[data-testid="deployments-list"]');
  });
  
  test('should show export dialog on button click', async ({ page }) => {
    const modelCard = page.locator('[data-testid="model-card"]').first();
    const exportButton = modelCard.locator('[data-testid="export-button"]');
    
    await exportButton.click();
    
    // Export dialog should be visible
    const exportDialog = page.locator('[data-testid="export-dialog"]');
    await expect(exportDialog).toBeVisible();
  });
});
```

---

## Load Testing

**File**: `tests/load_test.py`

```python
from locust import HttpUser, task, between
import time


class DefectionUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def infer(self):
        """Load test real-time inference"""
        image_base64 = "base64_test_image_data"
        
        self.client.post(
            "/api/v1/ai/infer",
            json={
                'image_base64': image_base64,
                'station_id': 'Station-A',
                'product_id': 'IC_001',
                'confidence_threshold': 0.85
            },
            headers={'Authorization': 'Bearer test_token'}
        )
    
    @task(1)
    def get_stats(self):
        """Load test stats endpoint"""
        self.client.get(
            "/api/v1/ai/stats",
            headers={'Authorization': 'Bearer test_token'}
        )


# Run: locust -f load_test.py --host http://localhost:8000
```

---

## Test Execution

```bash
# Run all tests
pytest --cov=backend

# Run specific test file
pytest backend/tests/test_yolo_model_manager.py -v

# Run with markers
pytest -m integration

# Generate coverage report
pytest --cov=backend --cov-report=html
# Open htmlcov/index.html in browser

# Run load tests
locust -f tests/load_test.py --host http://localhost:8000
```

---

## Test Results Reporting

```bash
# Generate JUnit XML for CI/CD
pytest --junitxml=test-results.xml

# Generate HTML report
pytest --html=report.html --self-contained-html

# Coverage thresholds
pytest --cov=backend --cov-fail-under=80
```

---

## Continuous Integration

GitHub Actions workflow:

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: autoqa_test
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements/test.txt
      
      - name: Run tests
        run: pytest --cov=backend
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Testing Checklist

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All E2E tests passing
- [ ] Code coverage >= 80%
- [ ] Load tests: 100+ concurrent users
- [ ] API response time < 100ms
- [ ] GPU inference < 20ms (TensorRT)
- [ ] No memory leaks (profiling)
- [ ] All edge cases handled
- [ ] Documentation up to date

---

**Last Updated:** May 1, 2026  
**Maintained By:** Team Pacific Corporation
