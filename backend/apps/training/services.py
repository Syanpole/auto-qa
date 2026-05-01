from .models import ModelAccess, ModelRegistry, StationModelAssignment


def resolve_station_model(station_id: str, product_id: str):
    return (
        StationModelAssignment.objects.select_related("model")
        .filter(station_id=station_id, product_id=product_id, is_active=True, model__is_active=True)
        .first()
    )


def user_can_access_model(user, model: ModelRegistry) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return ModelAccess.objects.filter(user=user, model=model, is_active=True).exists()
