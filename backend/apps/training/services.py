from .models import ModelAccess, ModelRegistry, StationModelAssignment
from apps.qa.models import QAStation, ProductProfile


def resolve_station_model(station_code: str, product_code: str):
    """
    Resolve the active model assigned to a station-product combination.
    
    Args:
        station_code: Station code (e.g., 'Station-A')
        product_code: Product code (e.g., 'IC_001')
    
    Returns:
        StationModelAssignment instance or None
    """
    try:
        station = QAStation.objects.get(station_code=station_code)
        product = ProductProfile.objects.get(product_code=product_code)
        return (
            StationModelAssignment.objects.select_related("model")
            .filter(station=station, product=product, is_active=True, model__is_active=True)
            .first()
        )
    except (QAStation.DoesNotExist, ProductProfile.DoesNotExist):
        return None


def user_can_access_model(user, model: ModelRegistry) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return ModelAccess.objects.filter(user=user, model=model, is_active=True).exists()
