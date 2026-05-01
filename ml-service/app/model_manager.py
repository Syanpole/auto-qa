import time
from typing import Any


class ModelManager:
    def __init__(self):
        self.active_family = "esmd_yolov26n"
        self.active_version = "v1.0.0"

    def infer(self, payload: dict[str, Any]) -> dict[str, Any]:
        start = time.time()
        threshold = float(payload.get("confidence_threshold", 0.85))

        # Placeholder deterministic sample; replace with Ultralytics/RT-DETR runtime.
        defects = [
            {
                "defect_class": "scratch",
                "confidence": 0.91,
                "bbox": [120.5, 88.2, 62.1, 24.0],
                "severity": "medium",
            }
        ]
        filtered = [d for d in defects if d["confidence"] >= threshold]
        verdict = "fail" if filtered else "pass"
        latency_ms = int((time.time() - start) * 1000)

        return {
            "status": "ok",
            "model_family": self.active_family,
            "model_version": self.active_version,
            "latency_ms": latency_ms,
            "verdict": verdict,
            "defects": filtered,
        }
