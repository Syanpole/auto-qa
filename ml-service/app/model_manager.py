"""
Model Manager wrapper for YOLO inference.
"""
import logging
from .yolo_model_manager import YOLOModelManager

logger = logging.getLogger(__name__)


class ModelManager:
    """Legacy interface for backward compatibility."""
    
    def __init__(self):
        self.manager = YOLOModelManager()
        self.active_family = "esmd_yolov26n"
        self.active_version = "v1.0.0"

    def infer(self, payload: dict) -> dict:
        """Run inference using YOLO model manager."""
        result = self.manager.infer(payload)
        
        # Convert to legacy format for compatibility
        return {
            "status": "ok",
            "model_family": self.active_family,
            "model_version": self.active_version,
            "latency_ms": int(result.inference_time_ms),
            "verdict": result.pass_fail_status.lower(),
            "defects": [
                {
                    "defect_class": d.class_name,
                    "confidence": d.confidence,
                    "bbox": d.bbox
                }
                for d in result.detections
            ],
        }


# Export for compatibility
__all__ = ["ModelManager"]
