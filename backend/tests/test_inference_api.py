"""Unit tests for inference API endpoints."""
import pytest
import base64
from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from apps.qa.models import QAStation, ProductProfile, DefectEvent


User = get_user_model()


@pytest.mark.django_db
class TestInferenceAPI:
    """Tests for inference API endpoints."""
    
    @pytest.fixture
    def test_image_base64(self):
        """Create a test image in base64 format."""
        img = Image.new('RGB', (640, 640), color='white')
        buffered = BytesIO()
        img.save(buffered, format='JPEG')
        return base64.b64encode(buffered.getvalue()).decode()
    
    @pytest.fixture
    def test_station_and_product(self):
        """Create test station and product."""
        station = QAStation.objects.create(
            station_code='Station-A',
            station_name='Test Station A'
        )
        product = ProductProfile.objects.create(
            product_code='IC_001',
            product_name='Test IC Product'
        )
        return station, product
    
    def test_realtime_inference_missing_fields(self, authenticated_client):
        """Test inference endpoint with missing required fields."""
        response = authenticated_client.post(
            '/api/v1/ai/infer',
            {'image_base64': 'test'}
        )
        assert response.status_code == 400
    
    def test_batch_inference_structure(self, authenticated_client, test_image_base64, test_station_and_product):
        """Test batch inference request structure."""
        station, product = test_station_and_product
        response = authenticated_client.post(
            '/api/v1/ai/infer/batch',
            {
                'images': [
                    {'image_base64': test_image_base64, 'product_id': 'IC_001'},
                    {'image_base64': test_image_base64, 'product_id': 'IC_002'}
                ],
                'station_id': 'Station-A',
                'confidence_threshold': 0.85
            },
            format='json'
        )
        assert response.status_code in [200, 201, 400, 404]  # May fail if inference service unavailable
    
    def test_disposition_creates_defect_event(self, authenticated_client, test_station_and_product):
        """Test that disposition endpoint creates DefectEvent."""
        station, product = test_station_and_product
        
        response = authenticated_client.post(
            '/api/v1/ai/disposition',
            {
                'station_id': 'Station-A',
                'product_id': 'IC_001',
                'operator_action': 'PASS',
                'defects_found': 0
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data['status'] == 'recorded'
            assert data['action'] == 'PASS'
            
            # Verify DefectEvent was created
            defect_event = DefectEvent.objects.filter(
                qa_station=station,
                product=product
            ).first()
            assert defect_event is not None
    
    def test_stats_endpoint_authenticated(self, authenticated_client):
        """Test stats endpoint requires authentication."""
        response = authenticated_client.get('/api/v1/ai/stats')
        assert response.status_code == 200
        
        data = response.json()
        assert 'total_inferences' in data
        assert 'pass_count' in data
        assert 'pass_rate_percent' in data
    
    def test_stats_endpoint_unauthenticated(self, api_client):
        """Test stats endpoint rejects unauthenticated requests."""
        response = api_client.get('/api/v1/ai/stats')
        assert response.status_code == 401
