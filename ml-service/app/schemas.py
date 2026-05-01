from pydantic import BaseModel, Field
from typing import Any


class InferenceRequest(BaseModel):
    station_id: str | None = None
    product_id: str | None = None
    image_uri: str | None = None
    image_b64: str | None = None
    mode: str = "realtime"
    confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    nms_threshold: float = Field(default=0.50, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DefectPrediction(BaseModel):
    defect_class: str
    confidence: float
    bbox: list[float]
    severity: str


class InferenceResponse(BaseModel):
    status: str
    model_family: str
    model_version: str
    latency_ms: int
    verdict: str
    defects: list[DefectPrediction]
