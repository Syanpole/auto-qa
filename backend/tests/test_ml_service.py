"""Unit tests for ML service components."""
import pytest
import tempfile
import os
from pathlib import Path


class TestYOLOModelManager:
    """Tests for YOLO Model Manager."""
    
    def test_model_manager_initialization(self):
        """Test YOLOModelManager can be initialized."""
        try:
            from ml_service.app.yolo_model_manager import YOLOModelManager
            manager = YOLOModelManager()
            assert manager is not None
            assert hasattr(manager, 'models')
            assert hasattr(manager, 'active_model')
        except ImportError:
            pytest.skip("ML service not available")
    
    def test_model_manager_has_required_methods(self):
        """Test YOLOModelManager has all required methods."""
        try:
            from ml_service.app.yolo_model_manager import YOLOModelManager
            manager = YOLOModelManager()
            
            required_methods = [
                'load_model',
                'infer',
                'batch_infer',
                'benchmark_model',
                'activate_model',
                'deactivate_model',
                'get_stats'
            ]
            
            for method in required_methods:
                assert hasattr(manager, method), f"Missing method: {method}"
                assert callable(getattr(manager, method)), f"{method} is not callable"
        except ImportError:
            pytest.skip("ML service not available")
    
    def test_stats_initialization(self):
        """Test that stats are initialized."""
        try:
            from ml_service.app.yolo_model_manager import YOLOModelManager
            manager = YOLOModelManager()
            stats = manager.get_stats()
            
            assert 'total_inferences' in stats
            assert 'total_defects_detected' in stats
            assert stats['total_inferences'] >= 0
        except ImportError:
            pytest.skip("ML service not available")


class TestExportPipeline:
    """Tests for YOLO export pipeline."""
    
    def test_export_pipeline_has_required_methods(self):
        """Test export pipeline has all export methods."""
        try:
            from backend.apps.training.yolo_export_pipeline import YOLOExportPipeline
            
            required_methods = [
                'export_onnx',
                'export_tensorrt',
                'export_openvino',
                'export_torchscript',
                'export_all'
            ]
            
            for method in required_methods:
                assert hasattr(YOLOExportPipeline, method), f"Missing method: {method}"
        except (ImportError, ModuleNotFoundError):
            pytest.skip("Export pipeline not available")
    
    def test_export_formats_list(self):
        """Test that export formats are properly defined."""
        try:
            from backend.apps.training.yolo_export_pipeline import YOLOExportPipeline
            
            expected_formats = ['tensorrt', 'onnx', 'openvino', 'torchscript']
            # Check that pipeline methods correspond to formats
            for fmt in expected_formats:
                method_name = f'export_{fmt}'
                assert hasattr(YOLOExportPipeline, method_name), f"Missing export method for {fmt}"
        except (ImportError, ModuleNotFoundError):
            pytest.skip("Export pipeline not available")


class TestPydanticSchemas:
    """Tests for Pydantic request/response schemas."""
    
    def test_inference_request_schema(self):
        """Test InferenceRequest schema validation."""
        try:
            from ml_service.app.schemas import InferenceRequest
            
            # Valid request
            valid_data = {
                'image_base64': 'base64_string',
                'station_id': 'Station-A',
                'product_id': 'IC_001',
                'model_name': 'ic_defect_v1',
                'confidence_threshold': 0.85
            }
            request = InferenceRequest(**valid_data)
            assert request.image_base64 == 'base64_string'
            assert request.confidence_threshold == 0.85
        except (ImportError, ModuleNotFoundError):
            pytest.skip("Pydantic schemas not available")
    
    def test_detection_result_schema(self):
        """Test DetectionResult schema."""
        try:
            from ml_service.app.schemas import DetectionResult
            
            detection = DetectionResult(
                class_id=0,
                class_name='scratch',
                confidence=0.92,
                bbox=[10, 20, 100, 150]
            )
            assert detection.class_name == 'scratch'
            assert detection.confidence == 0.92
            assert len(detection.bbox) == 4
        except (ImportError, ModuleNotFoundError):
            pytest.skip("Pydantic schemas not available")
    
    def test_inference_response_schema(self):
        """Test InferenceResponse schema."""
        try:
            from ml_service.app.schemas import InferenceResponse, DetectionResult
            
            detections = [
                DetectionResult(
                    class_id=0,
                    class_name='scratch',
                    confidence=0.92,
                    bbox=[10, 20, 100, 150]
                )
            ]
            
            response = InferenceResponse(
                status='success',
                pass_fail_status='REJECT',
                detections=detections,
                detection_count=1,
                inference_time_ms=12.5,
                model_used='ic_defect_v1'
            )
            
            assert response.status == 'success'
            assert response.detection_count == 1
            assert response.inference_time_ms == 12.5
        except (ImportError, ModuleNotFoundError):
            pytest.skip("Pydantic schemas not available")
