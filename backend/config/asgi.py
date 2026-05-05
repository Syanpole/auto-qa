import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from config.routing import websocket_urlpatterns

app_env = os.getenv("APP_ENV", "development").lower()
settings_module = "config.settings.prod" if app_env == "production" else "config.settings.dev"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
	{
		"http": django_asgi_app,
		"websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
	}
)
