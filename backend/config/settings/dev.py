from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]

REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = ["rest_framework.permissions.AllowAny"]

# PostgreSQL Configuration (default for dev)
DATABASES = {
	"default": {
		"ENGINE": "django.db.backends.postgresql",
		"NAME": "autoqa",
		"USER": "admin",
		"PASSWORD": "admin",
		"HOST": "localhost",
		"PORT": "5432",
	}
}

# Redis Configuration for Celery and Channels
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

CHANNEL_LAYERS = {
	"default": {
		"BACKEND": "channels_redis.core.RedisChannelLayer",
		"CONFIG": {
			"hosts": [("localhost", 6379)],
		},
	}
}
