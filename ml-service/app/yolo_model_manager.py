"""
YOLO Model Manager for Production Inference.

Handles model loading, inference, benchmarking, and lifecycle management.
"""
import io
import base64
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

import cv2
import numpy as np
import torch
from ultralytics import YOLO
from PIL import Image

from .schemas import InferenceResponse, ModelInfoResponse, DetectionResult

logger = logging.getLogger(__name__)


class YOLOModelManager:
    """
    Production-grade YOLO model manager with multi-model support.
    """
    
    def __init__(self):
        """Initialize model manager."""
        self.models: Dict[str, YOLO] = {}  # Loaded models
        self.active_model: Optional[str] = None  # Currently active model
        self.gpu_available = torch.cuda.is_available()
        
        # Statistics
        self.stats = {
            "total_inferences": 0,
            "total_defects_detected": 0,
            "inference_times_ms": [],
            "errors": 0,
            "last_reset": datetime.now().isoformat()
        }
        
        logger.info(f"YOLO Model Manager initialized (GPU available: {self.gpu_available})")
    
    def load_model(self, model_path: str, model_name: Optional[str] = None) -> Dict:
        """
        Load a YOLO model from file.
        
        Args:
            model_path: Path to model file (.pt, .onnx, .engine, etc)
            model_name: Optional custom name for the model
            
        Returns:
            Load status dictionary
        """
        try:
            path = Path(model_path)
            if not path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # Use filename as model name if not provided
            name = model_name or path.stem
            
            # Check if model already loaded
            if name in self.models:
                logger.info(f"Model {name} already loaded")
                return {"status": "already_loaded", "model": name}
            
            # Load model
            logger.info(f"Loading YOLO model: {model_path}")
            start_time = time.time()
            
            model = YOLO(model_path)
            load_time = time.time() - start_time
            
            self.models[name] = model
            
            # Set as active if first model
            if self.active_model is None:
                self.active_model = name
                logger.info(f"Model {name} set as active")
            
            logger.info(f"✓ Model {name} loaded successfully in {load_time:.2f}s")
            
            return {
                "status": "loaded",
                "model": name,
                "path": model_path,
                "load_time_seconds": load_time,
                "is_active": name == self.active_model
            }
        
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            self.stats["errors"] += 1
            raise
    
    def infer(self, payload: Dict) -> InferenceResponse:
        """
        Run inference on an image.
        
        Args:
            payload: Inference request payload with:
                - image_base64: Base64 encoded image
                - model_name: (optional) Model to use
                - confidence_threshold: (optional) Confidence threshold
                - iou_threshold: (optional) IOU threshold
                
        Returns:
            InferenceResponse with detections
        """
        start_time = time.time()
        
        try:
            # Get model
            model_name = payload.get("model_name", self.active_model)
            if not model_name or model_name not in self.models:
                raise ValueError(f"Model {model_name} not found")
            
            model = self.models[model_name]
            
            # Decode image
            image_base64 = payload.get("image_base64")
            if not image_base64:
                raise ValueError("image_base64 not provided")
            
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            image_np = np.array(image)
            
            # Inference parameters
            conf = float(payload.get("confidence_threshold", 0.85))
            iou = float(payload.get("iou_threshold", 0.50))
            
            # Run inference
            results = model.predict(
                source=image_np,
                conf=conf,
                iou=iou,
                imgsz=640,
                device=0 if self.gpu_available else 'cpu',
                verbose=False
            )
            
            inference_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Parse results
            detections = []
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None and len(result.boxes) > 0:
                    for box in result.boxes:
                        detection = DetectionResult(
                            class_id=int(box.cls.item()),
                            class_name=model.names[int(box.cls.item())],
                            confidence=float(box.conf.item()),
                            bbox=[
                                float(box.xyxy[0, 0].item()),
                                float(box.xyxy[0, 1].item()),
                                float(box.xyxy[0, 2].item()),
                                float(box.xyxy[0, 3].item()),
                            ]
                        )
                        detections.append(detection)
            
            # Update statistics
            self.stats["total_inferences"] += 1
            self.stats["total_defects_detected"] += len(detections)
            self.stats["inference_times_ms"].append(inference_time)
            
            # Determine status
            status = "REJECT" if detections else "PASS"
            
            return InferenceResponse(
                status="success",
                pass_fail_status=status,
                detections=detections,
                detection_count=len(detections),
                confidence_threshold=conf,
                inference_time_ms=inference_time,
                model_used=model_name,
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"Inference failed: {str(e)}")
            self.stats["errors"] += 1
            return InferenceResponse(
                status="error",
                pass_fail_status="ERROR",
                detections=[],
                detection_count=0,
                error_message=str(e),
                inference_time_ms=(time.time() - start_time) * 1000,
                model_used=model_name if 'model_name' in locals() else "unknown",
                timestamp=datetime.now().isoformat()
            )
    
    def infer_from_bytes(self, image_bytes: bytes, model_name: str = None, 
                        confidence_threshold: float = 0.85) -> InferenceResponse:
        """
        Run inference from raw image bytes.
        
        Args:
            image_bytes: Raw image bytes
            model_name: Model to use
            confidence_threshold: Confidence threshold
            
        Returns:
            InferenceResponse
        """
        base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
        payload = {
            "image_base64": base64_encoded,
            "model_name": model_name or self.active_model,
            "confidence_threshold": confidence_threshold
        }
        return self.infer(payload)
    
    def batch_infer(self, payload: Dict) -> List[Dict]:
        """
        Run inference on multiple images.
        
        Args:
            payload: Batch inference request with:
                - images: List of base64 encoded images
                - model_name: (optional) Model to use
                - confidence_threshold: (optional) Confidence threshold
                
        Returns:
            List of inference results
        """
        images = payload.get("images", [])
        model_name = payload.get("model_name", self.active_model)
        conf = payload.get("confidence_threshold", 0.85)
        
        logger.info(f"Batch inference: {len(images)} images with model {model_name}")
        
        results = []
        for idx, image_base64 in enumerate(images):
            result = self.infer({
                "image_base64": image_base64,
                "model_name": model_name,
                "confidence_threshold": conf
            })
            results.append(result.model_dump())
        
        return results
    
    def benchmark_model(self, model_name: str, num_runs: int = 100) -> Dict:
        """
        Benchmark a model's performance.
        
        Args:
            model_name: Model to benchmark
            num_runs: Number of inference runs
            
        Returns:
            Benchmark results
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        model = self.models[model_name]
        
        logger.info(f"Benchmarking {model_name} with {num_runs} runs")
        
        # Create dummy input
        dummy_input = np.random.rand(1, 3, 640, 640).astype(np.uint8)
        
        # Warmup
        for _ in range(10):
            model.predict(source=dummy_input, conf=0.5, verbose=False)
        
        # Benchmark
        times_ms = []
        for _ in range(num_runs):
            start = time.time()
            model.predict(source=dummy_input, conf=0.5, verbose=False)
            times_ms.append((time.time() - start) * 1000)
        
        times_ms = np.array(times_ms)
        
        return {
            "model": model_name,
            "num_runs": num_runs,
            "mean_latency_ms": float(np.mean(times_ms)),
            "min_latency_ms": float(np.min(times_ms)),
            "max_latency_ms": float(np.max(times_ms)),
            "p95_latency_ms": float(np.percentile(times_ms, 95)),
            "p99_latency_ms": float(np.percentile(times_ms, 99)),
            "throughput_fps": float(1000 / np.mean(times_ms)),
            "hardware": "GPU" if self.gpu_available else "CPU"
        }
    
    def activate_model(self, model_name: str) -> bool:
        """Activate a model for inference."""
        if model_name in self.models:
            self.active_model = model_name
            logger.info(f"Model {model_name} activated")
            return True
        return False
    
    def deactivate_model(self, model_name: str):
        """Deactivate a model."""
        if self.active_model == model_name:
            self.active_model = None
            logger.info(f"Model {model_name} deactivated")
    
    def unload_model(self, model_name: str):
        """Unload a model from memory."""
        if model_name in self.models:
            del self.models[model_name]
            if self.active_model == model_name:
                self.active_model = None
            logger.info(f"Model {model_name} unloaded")
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfoResponse]:
        """Get information about a model."""
        if model_name not in self.models:
            return None
        
        model = self.models[model_name]
        return ModelInfoResponse(
            model_name=model_name,
            is_active=model_name == self.active_model,
            class_names=model.names or [],
            input_shape=[640, 640, 3],
            device="GPU" if self.gpu_available else "CPU"
        )
    
    def list_loaded_models(self) -> List[str]:
        """List all loaded models."""
        return list(self.models.keys())
    
    def get_active_models_count(self) -> int:
        """Get count of loaded models."""
        return len(self.models)
    
    def is_gpu_available(self) -> bool:
        """Check if GPU is available."""
        return self.gpu_available
    
    def get_stats(self) -> Dict:
        """Get service statistics."""
        stats = self.stats.copy()
        
        if stats["inference_times_ms"]:
            times = np.array(stats["inference_times_ms"])
            stats["inference_times_ms"] = {
                "mean": float(np.mean(times)),
                "min": float(np.min(times)),
                "max": float(np.max(times)),
                "p95": float(np.percentile(times, 95))
            }
        
        stats["loaded_models"] = self.list_loaded_models()
        stats["active_model"] = self.active_model
        
        return stats
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "total_inferences": 0,
            "total_defects_detected": 0,
            "inference_times_ms": [],
            "errors": 0,
            "last_reset": datetime.now().isoformat()
        }
        logger.info("Statistics reset")
