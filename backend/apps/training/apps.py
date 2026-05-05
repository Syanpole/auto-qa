from django.apps import AppConfig


class TrainingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.training"

    def ready(self):
        from . import models_extended  # noqa: F401
