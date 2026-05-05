"""Unit tests for Django models."""
import pytest
from django.contrib.auth import get_user_model
from apps.training.models import AIModel, ModelExport, ModelDeployment
from apps.qa.models import QAStation, ProductProfile


User = get_user_model()


@pytest.mark.django_db
class TestAIModel:
    """Tests for AIModel."""
    
    def test_create_ai_model(self):
        """Test creating an AIModel."""
        model = AIModel.objects.create(
            model_name='ic_defect_v1',
            version_tag='1.0.0',
            model_family='yolov8',
            defect_types=['scratch', 'crack', 'chip'],
            status='draft',
            is_active=False
        )
        assert model.model_name == 'ic_defect_v1'
        assert model.version_tag == '1.0.0'
        assert model.status == 'draft'
        assert model.is_active is False
    
    def test_ai_model_unique_constraint(self):
        """Test that model name-version combination is unique."""
        AIModel.objects.create(
            model_name='ic_v1',
            version_tag='1.0.0',
            model_family='yolov8',
            status='draft'
        )
        
        with pytest.raises(Exception):  # IntegrityError
            AIModel.objects.create(
                model_name='ic_v1',
                version_tag='1.0.0',
                model_family='yolov8',
                status='draft'
            )
    
    def test_activate_model(self):
        """Test activating a model."""
        model = AIModel.objects.create(
            model_name='ic_v1',
            version_tag='1.0.0',
            model_family='yolov8',
            status='production',
            is_active=False
        )
        model.is_active = True
        model.save()
        
        refreshed = AIModel.objects.get(id=model.id)
        assert refreshed.is_active is True


@pytest.mark.django_db
class TestModelExport:
    """Tests for ModelExport."""
    
    def test_create_export(self):
        """Test creating a ModelExport."""
        model = AIModel.objects.create(
            model_name='ic_v1',
            version_tag='1.0.0',
            model_family='yolov8',
            status='production'
        )
        
        export = ModelExport.objects.create(
            ai_model=model,
            export_format='tensorrt',
            status='completed',
            file_path='exports/ic_v1.engine'
        )
        
        assert export.export_format == 'tensorrt'
        assert export.status == 'completed'
        assert export.ai_model == model
    
    def test_export_with_metrics(self):
        """Test export with performance metrics."""
        model = AIModel.objects.create(
            model_name='ic_v1',
            version_tag='1.0.0',
            model_family='yolov8',
            status='production'
        )
        
        export = ModelExport.objects.create(
            ai_model=model,
            export_format='tensorrt',
            status='completed',
            file_path='exports/ic_v1.engine',
            inference_time_ms=12.5,
            throughput_fps=80,
            benchmark_hardware='RTX 4090'
        )
        
        assert export.inference_time_ms == 12.5
        assert export.throughput_fps == 80


@pytest.mark.django_db
class TestModelDeployment:
    """Tests for ModelDeployment."""
    
    def test_create_deployment(self):
        """Test creating a ModelDeployment."""
        model = AIModel.objects.create(
            model_name='ic_v1',
            version_tag='1.0.0',
            model_family='yolov8',
            status='production',
            is_active=True
        )
        
        deployment = ModelDeployment.objects.create(
            ai_model=model,
            deployment_target='production',
            status='active'
        )
        
        assert deployment.status == 'active'
        assert deployment.deployment_target == 'production'
    
    def test_deployment_tracking(self):
        """Test deployment metrics tracking."""
        model = AIModel.objects.create(
            model_name='ic_v1',
            version_tag='1.0.0',
            model_family='yolov8',
            status='production',
            is_active=True
        )
        
        deployment = ModelDeployment.objects.create(
            ai_model=model,
            deployment_target='production',
            status='active',
            inference_requests_count=100,
            error_count=5
        )
        
        assert deployment.inference_requests_count == 100
        assert deployment.error_count == 5
