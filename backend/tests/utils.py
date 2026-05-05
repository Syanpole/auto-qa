"""Test utilities and helpers."""
import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager


@contextmanager
def temporary_model_file():
    """Context manager for creating temporary model files for testing."""
    temp_dir = tempfile.mkdtemp()
    try:
        model_path = Path(temp_dir) / 'test_model.pt'
        model_path.touch()
        yield model_path
    finally:
        shutil.rmtree(temp_dir)


def create_test_image_path():
    """Create a temporary test image file."""
    temp_dir = tempfile.mkdtemp()
    image_path = Path(temp_dir) / 'test_image.jpg'
    
    # Create a minimal JPEG file
    image_path.touch()
    return image_path


class APITestMixin:
    """Mixin for API test classes."""
    
    def assert_response_status(self, response, expected_status):
        """Assert response status code."""
        assert response.status_code == expected_status, \
            f"Expected status {expected_status}, got {response.status_code}. Response: {response.content}"
    
    def assert_response_has_key(self, response, key):
        """Assert response JSON has key."""
        data = response.json()
        assert key in data, f"Response missing key: {key}. Response: {data}"
    
    def assert_response_data(self, response, expected_data):
        """Assert response JSON data matches expected."""
        data = response.json()
        for key, value in expected_data.items():
            assert key in data, f"Response missing key: {key}"
            assert data[key] == value, f"Expected {key}={value}, got {data[key]}"
