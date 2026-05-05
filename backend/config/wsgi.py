import os
from django.core.wsgi import get_wsgi_application

app_env = os.getenv("APP_ENV", "development").lower()
settings_module = "config.settings.prod" if app_env == "production" else "config.settings.dev"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
application = get_wsgi_application()
