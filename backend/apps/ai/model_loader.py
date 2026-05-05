"""
Model loading and initialization service.
Handles registration of models in both cache registry and database.
"""
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from django.conf import settings
from django.utils import timezone
from .models import InferenceModel
from .model_registry import get_registry

logger = logging.getLogger(__name__)


class ModelLoaderService:
    """Service for loading, registering, and activating inference models."""
    
    @staticmethod
    def load_model_from_file(
        file_path: str,
        model_name: str,
        description: str = "",
        confidence_threshold: float = 0.85,
        iou_threshold: float = 0.50,
        deployed_by_user = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Load a model from file and register it in both cache and database.
        
        Args:
            file_path: Path to .pt model file
            model_name: Name to register as (e.g., 'ic_defect_v1')
            description: Human-readable description
            confidence_threshold: Default confidence threshold
            iou_threshold: Default IOU threshold
            deployed_by_user: User object who deployed the model
            **kwargs: Additional metadata (version, architecture, etc.)
        
        Returns:
            Dict with load status
        """
        try:
            # Validate file exists
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Model file not found: {file_path}")
            
            file_size_mb = path.stat().st_size / (1024 * 1024)
            logger.info(f"Loading model: {model_name} ({file_size_mb:.1f} MB)")
            
            # Register in database
            model_obj, created = InferenceModel.objects.update_or_create(
                name=model_name,
                defaults={
                    "file_path": str(file_path),
                    "model_format": "pytorch",
                    "is_enabled": True,
                    "confidence_threshold": confidence_threshold,
                    "iou_threshold": iou_threshold,
                    "description": description,
                    "deployed_by": deployed_by_user,
                    "last_activated_at": timezone.now(),
                    **kwargs
                }
            )
            
            logger.info(f"Model {'created' if created else 'updated'}: {model_name}")
            
            # Register in cache registry
            registry = get_registry()
            metadata = {
                "confidence_threshold": confidence_threshold,
                "iou_threshold": iou_threshold,
                "file_size_mb": file_size_mb,
                "model_id": str(model_obj.id),
                **kwargs
            }
            
            registry.register_model(
                model_name=model_name,
                model_path=str(file_path),
                is_active=kwargs.get('is_active', False),
                metadata=metadata
            )
            
            return {
                "status": "loaded",
                "model_name": model_name,
                "model_id": str(model_obj.id),
                "file_path": str(file_path),
                "file_size_mb": file_size_mb,
                "is_active": model_obj.is_active,
                "created": created
            }
        
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {str(e)}")
            raise
    
    @staticmethod
    def activate_model(model_name: str) -> Dict[str, Any]:
        """
        Activate a model for production inference.
        
        Args:
            model_name: Name of model to activate
        
        Returns:
            Activation status dict
        """
        try:
            # Update database
            InferenceModel.objects.filter(is_active=True).update(is_active=False)
            model_obj = InferenceModel.objects.get(name=model_name)
            model_obj.is_active = True
            model_obj.last_activated_at = timezone.now()
            model_obj.save()
            
            # Update cache registry
            registry = get_registry()
            registry.set_active_model(model_name)
            
            logger.info(f"Model activated: {model_name}")
            
            return {
                "status": "activated",
                "model_name": model_name,
                "model_id": str(model_obj.id),
                "file_path": model_obj.file_path
            }
        
        except InferenceModel.DoesNotExist:
            logger.error(f"Model not found: {model_name}")
            raise ValueError(f"Model {model_name} not found in database")
        except Exception as e:
            logger.error(f"Failed to activate model {model_name}: {str(e)}")
            raise
    
    @staticmethod
    def get_active_model() -> Optional[InferenceModel]:
        """Get the currently active model."""
        try:
            return InferenceModel.objects.get(is_active=True, is_enabled=True)
        except InferenceModel.DoesNotExist:
            return None
    
    @staticmethod
    def list_available_models() -> list:
        """List all enabled models."""
        return list(
            InferenceModel.objects.filter(is_enabled=True).values(
                'id', 'name', 'is_active', 'version', 'file_path', 'confidence_threshold'
            ).order_by('-created_at')
        )
