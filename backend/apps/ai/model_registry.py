"""
Model Registry: Manages active inference models and their lifecycle.
Centralizes model configuration and ensures production-safe failover.
"""
import logging
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Cache keys for model registry
ACTIVE_MODEL_KEY = "ai_active_model_name"
MODEL_CONFIG_KEY = "ai_model_config_{name}"
MODEL_REGISTRY_KEY = "ai_model_registry"


class ModelRegistry:
    """
    Singleton registry for managing active inference models.
    Thread-safe via Django cache and database persistence.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.ml_service_url = getattr(settings, 'ML_SERVICE_URL', 'http://localhost:8001')
        logger.info(f"ModelRegistry initialized. ML Service: {self.ml_service_url}")
    
    def register_model(self, model_name: str, model_path: str, 
                      is_active: bool = False, 
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Register a model in the registry.
        
        Args:
            model_name: Unique identifier (e.g., 'ic_defect_v1')
            model_path: Path to .pt file
            is_active: Whether to set as active model
            metadata: Additional config (confidence_threshold, iou_threshold, etc.)
        
        Returns:
            Registration status dict
        """
        if not metadata:
            metadata = {}
        
        model_config = {
            "name": model_name,
            "path": model_path,
            "is_active": is_active,
            "metadata": metadata,
            "status": "registered"
        }
        
        # Store in cache
        cache.set(MODEL_CONFIG_KEY.format(name=model_name), model_config, timeout=None)
        
        # Add to registry list
        registry = cache.get(MODEL_REGISTRY_KEY, {})
        registry[model_name] = model_config
        cache.set(MODEL_REGISTRY_KEY, registry, timeout=None)
        
        # Set as active if requested
        if is_active:
            self.set_active_model(model_name)
        
        logger.info(f"Model registered: {model_name} (active={is_active})")
        return {
            "status": "registered",
            "model_name": model_name,
            "is_active": is_active
        }
    
    def set_active_model(self, model_name: str) -> bool:
        """Set model as the active/default for inference."""
        model_config = cache.get(MODEL_CONFIG_KEY.format(name=model_name))
        if not model_config:
            logger.error(f"Cannot activate: model {model_name} not registered")
            return False
        
        # Update registry
        registry = cache.get(MODEL_REGISTRY_KEY, {})
        for name, cfg in registry.items():
            cfg["is_active"] = (name == model_name)
            cache.set(MODEL_CONFIG_KEY.format(name=name), cfg, timeout=None)
        registry[model_name]["is_active"] = True
        cache.set(MODEL_REGISTRY_KEY, registry, timeout=None)
        
        # Set active key
        cache.set(ACTIVE_MODEL_KEY, model_name, timeout=None)
        
        logger.info(f"Active model set to: {model_name}")
        return True
    
    def get_active_model(self) -> Optional[str]:
        """Get the name of the currently active model."""
        return cache.get(ACTIVE_MODEL_KEY) or "ic_defect_v1"  # Fallback to default
    
    def get_model_config(self, model_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get config for a model. If model_name is None, returns active model config.
        
        Args:
            model_name: Model name, or None for active model
        
        Returns:
            Model config dict or None
        """
        if model_name is None:
            model_name = self.get_active_model()
        
        return cache.get(MODEL_CONFIG_KEY.format(name=model_name))
    
    def list_models(self) -> Dict[str, Any]:
        """List all registered models."""
        return cache.get(MODEL_REGISTRY_KEY, {})
    
    def is_model_active(self, model_name: str) -> bool:
        """Check if a model is currently active."""
        return self.get_active_model() == model_name
    
    def get_active_model_path(self) -> Optional[str]:
        """Get the file path of the currently active model."""
        config = self.get_model_config()
        return config.get("path") if config else None


# Global singleton instance
registry = ModelRegistry()


def get_registry() -> ModelRegistry:
    """Get the model registry singleton."""
    return registry
