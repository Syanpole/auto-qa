import logging
import os
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from .yolo_model_manager import YOLOModelManager
from .schemas import InferenceRequest, InferenceResponse, ModelInfoResponse, BatchInferenceRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AUTO QA YOLO Inference Service",
    description="Production-grade YOLO inference engine for IC defect detection",
    version="2.0.0"
)

# Initialize model manager
manager = YOLOModelManager()


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """
    Load production model on service startup.
    Automatically initializes ic_defect_v1 if file exists.
    """
    # Try to load production model from environment variable or default path
    model_path = os.getenv('PRODUCTION_MODEL_PATH')
    if not model_path:
        # Default location relative to workspace
        default_path = Path(__file__).parent.parent.parent.parent / \
                      "backend" / "models_registry" / "deployed_models" / "tpcyolov26nv21gs.pt"
        if default_path.exists():
            model_path = str(default_path)
    
    if model_path and Path(model_path).exists():
        try:
            logger.info(f"Loading production model: {model_path}")
            result = manager.load_model(model_path, "ic_defect_v1")
            logger.info(f"Production model loaded: {result}")
        except Exception as e:
            logger.warning(f"Failed to load production model on startup: {e}")
    else:
        logger.warning("Production model not found at startup; using lazy loading")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("ML service shutting down")


# ==================== Health & Status Endpoints ====================

@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "yolo-ml-service",
        "active_models": manager.get_active_models_count(),
        "gpu_available": manager.is_gpu_available()
    }


@app.get("/models")
def list_models() -> dict:
    """List all available models."""
    return {
        "models": manager.list_loaded_models(),
        "total": len(manager.list_loaded_models())
    }


@app.get("/models/{model_name}")
def model_info(model_name: str) -> ModelInfoResponse:
    """Get information about a specific model."""
    info = manager.get_model_info(model_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
    return info


# ==================== Inference Endpoints ====================

@app.post("/v1/infer", response_model=InferenceResponse)
def infer(request: InferenceRequest) -> InferenceResponse:
    """
    Single image inference endpoint.
    
    Detects defects in a single image using specified model.
    """
    try:
        logger.info(f"Inference request: model={request.model_name}, confidence={request.confidence_threshold}")
        result = manager.infer(request.model_dump())
        return result
    except Exception as e:
        logger.error(f"Inference failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.post("/v1/infer/batch")
def batch_infer(request: BatchInferenceRequest) -> dict:
    """
    Batch inference endpoint.
    
    Process multiple images in a single request for higher throughput.
    """
    try:
        logger.info(f"Batch inference request: {len(request.images)} images")
        results = manager.batch_infer(request.model_dump())
        return {
            "status": "completed",
            "results": results,
            "total_processed": len(results)
        }
    except Exception as e:
        logger.error(f"Batch inference failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch inference failed: {str(e)}")


@app.post("/v1/infer/stream")
async def stream_infer(file: UploadFile = File(...)):
    """
    Stream inference endpoint.
    
    Process uploaded image file directly without base64 encoding.
    """
    try:
        logger.info(f"Stream inference: {file.filename}")
        contents = await file.read()
        result = manager.infer_from_bytes(
            image_bytes=contents,
            model_name="default",
            confidence_threshold=0.85
        )
        return result
    except Exception as e:
        logger.error(f"Stream inference failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stream inference failed: {str(e)}")


# ==================== Model Management Endpoints ====================

@app.post("/v1/models/load")
def load_model(model_path: str, model_name: str = None) -> dict:
    """
    Load a model from file.
    
    Args:
        model_path: Path to .pt, .onnx, or .engine file
        model_name: Custom name for the model
    """
    try:
        logger.info(f"Loading model from {model_path}")
        result = manager.load_model(model_path, model_name)
        return result
    except Exception as e:
        logger.error(f"Model loading failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Model loading failed: {str(e)}")


@app.post("/v1/models/activate")
def activate_model(model_name: str) -> dict:
    """Activate a model for inference."""
    result = manager.activate_model(model_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
    return {"status": "activated", "model": model_name}


@app.post("/v1/models/deactivate")
def deactivate_model(model_name: str) -> dict:
    """Deactivate a model."""
    manager.deactivate_model(model_name)
    return {"status": "deactivated", "model": model_name}


@app.post("/v1/models/unload")
def unload_model(model_name: str) -> dict:
    """Unload a model from memory."""
    manager.unload_model(model_name)
    return {"status": "unloaded", "model": model_name}


# ==================== Benchmark Endpoints ====================

@app.post("/v1/benchmark")
def benchmark_model(model_name: str, num_runs: int = 100) -> dict:
    """
    Run performance benchmark on a model.
    
    Args:
        model_name: Name of model to benchmark
        num_runs: Number of inference runs
    """
    try:
        logger.info(f"Benchmarking {model_name} with {num_runs} runs")
        results = manager.benchmark_model(model_name, num_runs)
        return results
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Benchmark failed: {str(e)}")


# ==================== Statistics Endpoints ====================

@app.get("/v1/stats")
def get_stats() -> dict:
    """Get service statistics."""
    return manager.get_stats()


@app.post("/v1/stats/reset")
def reset_stats() -> dict:
    """Reset service statistics."""
    manager.reset_stats()
    return {"status": "stats_reset"}


# ==================== Error Handlers ====================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
