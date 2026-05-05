"""
Pydantic schemas for YOLO inference service.
"""
from pydantic import BaseModel, Field
from typing import Any, Optional, List
from datetime import datetime


# ==================== Detection Results ====================

class DetectionResult(BaseModel):
    """Single detection result."""
    class_id: int
    class_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: List[float] = Field(..., description="[x1, y1, x2, y2] bounding box coordinates")


class DefectPrediction(BaseModel):
    """Legacy defect prediction format."""
    defect_class: str
    confidence: float
    bbox: List[float]
    severity: Optional[str] = "medium"


# ==================== Inference Requests ====================

class InferenceRequest(BaseModel):
    """Single image inference request."""
    station_id: Optional[str] = None
    product_id: Optional[str] = None
    image_base64: str = Field(..., description="Base64 encoded image")
    model_name: Optional[str] = None
    mode: str = Field(default="realtime", description="'realtime' or 'batch'")
    confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.50, ge=0.0, le=1.0)
    metadata: dict = Field(default_factory=dict)


class BatchInferenceRequest(BaseModel):
    """Batch inference request for multiple images."""
    images: List[str] = Field(..., description="List of base64 encoded images")
    model_name: Optional[str] = None
    confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.50, ge=0.0, le=1.0)


# ==================== Inference Responses ====================

class InferenceResponse(BaseModel):
    """Inference response with detection results."""
    status: str = Field(..., description="'success' or 'error'")
    pass_fail_status: str = Field(..., description="'PASS', 'REJECT', or 'ERROR'")
    detections: List[DetectionResult] = Field(default_factory=list)
    detection_count: int
    confidence_threshold: float
    iou_threshold: Optional[float] = None
    inference_time_ms: float
    model_used: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    def model_dump(self, **kwargs) -> dict:
        """Override to handle datetime serialization."""
        data = super().model_dump(**kwargs)
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        return data


class LegacyInferenceResponse(BaseModel):
    """Legacy inference response for backward compatibility."""
    status: str
    model_family: str
    model_version: str
    latency_ms: int
    verdict: str
    defects: List[DefectPrediction]


# ==================== Model Management ====================

class ModelInfoResponse(BaseModel):
    """Information about a loaded model."""
    model_name: str
    is_active: bool
    class_names: List[str] = Field(default_factory=list, description="Detected object classes")
    input_shape: List[int] = Field(default=[640, 640, 3])
    device: str = Field(..., description="'GPU' or 'CPU'")


class ModelLoadResponse(BaseModel):
    """Response from model loading."""
    status: str = Field(..., description="'loaded', 'already_loaded', or 'failed'")
    model: str
    path: Optional[str] = None
    load_time_seconds: Optional[float] = None
    is_active: Optional[bool] = False


# ==================== Benchmarking ====================

class BenchmarkResult(BaseModel):
    """Model benchmark result."""
    model: str
    num_runs: int
    mean_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: Optional[float] = None
    throughput_fps: float
    hardware: str


# ==================== Service Statistics ====================

class ServiceStats(BaseModel):
    """Service statistics."""
    total_inferences: int
    total_defects_detected: int
    errors: int
    loaded_models: List[str]
    active_model: Optional[str]
    gpu_available: bool
    uptime_seconds: Optional[int] = None

