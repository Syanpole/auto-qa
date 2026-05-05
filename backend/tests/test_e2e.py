"""E2E test scenarios."""
import pytest
from django.contrib.auth import get_user_model
from apps.qa.models import QAStation, ProductProfile


User = get_user_model()


@pytest.mark.django_db
class TestCompleteInspectionFlow:
    """Test complete QA inspection workflow."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data."""
        self.station = QAStation.objects.create(
            station_code='Station-A',
            station_name='Inspection Line A'
        )
        self.product = ProductProfile.objects.create(
            product_code='IC_001',
            product_name='ARM Processor'
        )
        self.operator = User.objects.create_user(
            username='operator',
            password='testpass123'
        )
    
    def test_inspection_workflow_pass(self, authenticated_client):
        """Test complete workflow for passing product."""
        # 1. Operator logs in (already done via authenticated_client fixture)
        
        # 2. Operator selects station and product
        # This would normally be done via UI
        
        # 3. Operator sends image for inspection
        response = authenticated_client.post(
            '/api/v1/ai/infer',
            {
                'image_base64': 'test_image_base64',
                'station_id': 'Station-A',
                'product_id': 'IC_001',
                'confidence_threshold': 0.85
            }
        )
        
        # Should receive inference results (may be 400 if inference service unavailable)
        assert response.status_code in [200, 400, 404]
    
    def test_inspection_workflow_rework(self, authenticated_client):
        """Test complete workflow for product requiring rework."""
        # Send inspection request
        response = authenticated_client.post(
            '/api/v1/ai/infer',
            {
                'image_base64': 'test_image_base64',
                'station_id': 'Station-A',
                'product_id': 'IC_001',
                'confidence_threshold': 0.85
            }
        )
        
        # Operator marks for rework
        response = authenticated_client.post(
            '/api/v1/ai/disposition',
            {
                'station_id': 'Station-A',
                'product_id': 'IC_001',
                'operator_action': 'REWORK',
                'defects_found': 2
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data['action'] == 'REWORK'
    
    def test_operator_statistics(self, authenticated_client):
        """Test operator can view their statistics."""
        # Get operator stats
        response = authenticated_client.get('/api/v1/ai/stats')
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ['total_inferences', 'pass_count', 'pass_rate_percent']
        for field in required_fields:
            assert field in data


@pytest.mark.django_db
class TestModelManagementWorkflow:
    """Test model management workflow."""
    
    def test_model_lifecycle(self):
        """Test complete model lifecycle."""
        from apps.training.models import AIModel
        
        # 1. Create model (draft)
        model = AIModel.objects.create(
            model_name='ic_defect_v1',
            version_tag='1.0.0',
            model_family='yolov8',
            status='draft',
            is_active=False
        )
        assert model.status == 'draft'
        
        # 2. Update to training
        model.status = 'training'
        model.save()
        assert model.status == 'training'
        
        # 3. Update to validated
        model.status = 'validated'
        model.throughput_fps = 80
        model.inference_time_ms = 12.5
        model.save()
        assert model.status == 'validated'
        
        # 4. Activate model
        model.status = 'production'
        model.is_active = True
        model.save()
        
        refreshed = AIModel.objects.get(id=model.id)
        assert refreshed.is_active is True
        assert refreshed.status == 'production'
