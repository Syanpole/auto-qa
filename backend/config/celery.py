import os
from celery import Celery

app_env = os.getenv("APP_ENV", "development").lower()
settings_module = "config.settings.prod" if app_env == "production" else "config.settings.dev"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

app = Celery("autoqa")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
