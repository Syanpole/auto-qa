from fastapi import FastAPI
from .model_manager import ModelManager
from .schemas import InferenceRequest, InferenceResponse

app = FastAPI(title="AUTO QA Inference Service", version="1.0.0")
manager = ModelManager()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ml-service"}


@app.post("/v1/infer", response_model=InferenceResponse)
def infer(request: InferenceRequest):
    return manager.infer(request.model_dump())
