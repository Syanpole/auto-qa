"""Pytest configuration and fixtures for backend tests."""
import os
import django
import pytest
from django.conf import settings
from django.test.utils import get_runner
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model


def pytest_configure():
    """Configure Django settings for pytest."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
    django.setup()


@pytest.fixture(scope='session')
def django_db_setup():
    """Configure test database."""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


@pytest.fixture
def api_client():
    """Return a DRF API test client."""
    return APIClient()


@pytest.fixture
def authenticated_user():
    """Create a test user."""
    User = get_user_model()
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    return user


@pytest.fixture
def authenticated_client(api_client, authenticated_user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=authenticated_user)
    return api_client
