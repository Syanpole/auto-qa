"""
Integration test script for the production YOLO model setup.
Demonstrates loading the model and running inferences end-to-end.
"""
import os
import sys
import time
import requests
import base64
from pathlib import Path
from PIL import Image
import io

# Configuration
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8001")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
# Correct path: from ml-service/scripts up 3 levels to project root, then to backend
MODEL_PATH = Path(__file__).parent.parent.parent / "backend" / "models_registry" / "deployed_models" / "tpcyolov26nv21gs.pt"
MODEL_NAME = "ic_defect_v1"


def create_test_image(width=640, height=640, color=(200, 100, 100)):
    """Create a simple test image."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def check_ml_service():
    """Check if ML service is running."""
    try:
        r = requests.get(f"{ML_SERVICE_URL}/health", timeout=5)
        print(f"OK ML Service is running")
        print(f"  Active models: {r.json().get('active_models')}")
        print(f"  GPU available: {r.json().get('gpu_available')}")
        return True
    except Exception as e:
        print(f"FAIL ML Service error: {e}")
        return False


def load_model_in_ml_service():
    """Load the model in the ML service."""
    print(f"\n{'='*70}")
    print("STEP 1: Loading model in ML service")
    print(f"{'='*70}")
    
    if not MODEL_PATH.exists():
        print(f"FAIL Model file not found: {MODEL_PATH}")
        return False
    
    print(f"Model path: {MODEL_PATH}")
    print(f"File size: {MODEL_PATH.stat().st_size / (1024*1024):.1f} MB")
    
    try:
        r = requests.post(
            f"{ML_SERVICE_URL}/v1/models/load",
            params={
                "model_path": str(MODEL_PATH),
                "model_name": MODEL_NAME
            },
            timeout=120
        )
        if r.status_code == 400 or r.status_code == 422:
            # Query params didn't work, try JSON body
            r = requests.post(
                f"{ML_SERVICE_URL}/v1/models/load",
                json={
                    "model_path": str(MODEL_PATH),
                    "model_name": MODEL_NAME
                },
                timeout=120
            )
        r.raise_for_status()
        result = r.json()
        print(f"OK Model loaded: {result.get('status')}")
        print(f"  Load time: {result.get('load_time_seconds', 'N/A')} seconds")
        return True
    except Exception as e:
        print(f"FAIL Failed to load model: {e}")
        return False


def verify_model():
    """Verify model is loaded and accessible."""
    print(f"\n{'='*70}")
    print("STEP 2: Verifying model")
    print(f"{'='*70}")
    
    try:
        r = requests.get(f"{ML_SERVICE_URL}/models/{MODEL_NAME}", timeout=10)
        r.raise_for_status()
        info = r.json()
        print(f"OK Model verified: {info.get('model_name')}")
        print(f"  Device: {info.get('device')}")
        print(f"  Classes: {len(info.get('class_names', []))}")
        print(f"  Active: {info.get('is_active')}")
        return True
    except Exception as e:
        print(f"FAIL Model verification failed: {e}")
        return False


def list_models():
    """List all loaded models."""
    print(f"\n{'='*70}")
    print("STEP 3: Listing available models")
    print(f"{'='*70}")
    
    try:
        r = requests.get(f"{ML_SERVICE_URL}/models", timeout=10)
        r.raise_for_status()
        models = r.json()
        print(f"OK Loaded models: {models.get('total')}")
        for model in models.get('models', []):
            print(f"  - {model}")
        return True
    except Exception as e:
        print(f"FAIL Failed to list models: {e}")
        return False


def run_inference_test():
    """Run test inference through the ML service."""
    print(f"\n{'='*70}")
    print("STEP 4: Running test inference")
    print(f"{'='*70}")
    
    # Create test image
    print("Creating test image...")
    image_b64 = create_test_image()
    print(f"  Image size: {len(image_b64)} bytes (base64)")
    
    # Run inference
    print("Running inference...")
    payload = {
        "image_base64": image_b64,
        "model_name": MODEL_NAME,
        "confidence_threshold": 0.85,
        "station_id": "Station-A",
        "product_id": "IC_001"
    }
    
    try:
        start = time.time()
        r = requests.post(
            f"{ML_SERVICE_URL}/v1/infer",
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        latency = time.time() - start
        
        result = r.json()
        print(f"OK Inference completed in {latency:.2f} seconds")
        print(f"  Status: {result.get('status')}")
        print(f"  Verdict: {result.get('pass_fail_status')}")
        print(f"  Detections: {result.get('detection_count')}")
        print(f"  Latency: {result.get('inference_time_ms')} ms")
        print(f"  Model used: {result.get('model_used')}")
        
        if result.get('detections'):
            print("  Detected objects:")
            for det in result.get('detections', [])[:3]:  # Show first 3
                print(f"    - {det.get('class_name')}: {det.get('confidence'):.3f}")
        
        return True
    except Exception as e:
        print(f"FAIL Inference failed: {e}")
        return False


def run_batch_inference_test():
    """Run batch inference test."""
    print(f"\n{'='*70}")
    print("STEP 5: Running batch inference test")
    print(f"{'='*70}")
    
    # Create multiple test images
    print("Creating 3 test images...")
    images = [create_test_image() for _ in range(3)]
    print(f"  Total batch size: {sum(len(img) for img in images) / 1024:.1f} KB")
    
    payload = {
        "images": images,
        "model_name": MODEL_NAME,
        "confidence_threshold": 0.85
    }
    
    try:
        start = time.time()
        r = requests.post(
            f"{ML_SERVICE_URL}/v1/infer/batch",
            json=payload,
            timeout=60
        )
        r.raise_for_status()
        latency = time.time() - start
        
        result = r.json()
        print(f"OK Batch inference completed in {latency:.2f} seconds")
        print(f"  Total processed: {result.get('total_processed')}")
        print(f"  Status: {result.get('status')}")
        
        if result.get('results'):
            print("  Results summary:")
            for idx, res in enumerate(result.get('results', [])[:3]):
                print(f"    [{idx+1}] {res.get('pass_fail_status')} - {res.get('detection_count')} detections")
        
        return True
    except Exception as e:
        print(f"FAIL Batch inference failed: {e}")
        return False


def get_stats():
    """Get service statistics."""
    print(f"\n{'='*70}")
    print("STEP 6: Service Statistics")
    print(f"{'='*70}")
    
    try:
        r = requests.get(f"{ML_SERVICE_URL}/v1/stats", timeout=10)
        r.raise_for_status()
        stats = r.json()
        
        print(f"OK Service stats retrieved")
        print(f"  Total inferences: {stats.get('total_inferences')}")
        print(f"  Total defects detected: {stats.get('total_defects_detected')}")
        print(f"  Errors: {stats.get('errors')}")
        print(f"  Loaded models: {stats.get('loaded_models')}")
        print(f"  Active model: {stats.get('active_model')}")
        
        if stats.get('inference_times_ms'):
            times = stats['inference_times_ms']
            print(f"  Latency stats (ms):")
            print(f"    - Mean: {times.get('mean'):.2f}")
            print(f"    - Min: {times.get('min'):.2f}")
            print(f"    - Max: {times.get('max'):.2f}")
            print(f"    - P95: {times.get('p95'):.2f}")
        
        return True
    except Exception as e:
        print(f"FAIL Failed to get stats: {e}")
        return False


def main():
    """Run the complete integration test suite."""
    print("\n" + "="*70)
    print("AUTO-QA YOLO MODEL INTEGRATION TEST")
    print("="*70)
    print(f"ML Service URL: {ML_SERVICE_URL}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Model Name: {MODEL_NAME}")
    print(f"Model Path: {MODEL_PATH}")
    
    steps = [
        ("ML Service Health Check", check_ml_service),
        ("Load Model", load_model_in_ml_service),
        ("Verify Model", verify_model),
        ("List Models", list_models),
        ("Single Inference", run_inference_test),
        ("Batch Inference", run_batch_inference_test),
        ("Service Stats", get_stats),
    ]
    
    results = {}
    for step_name, step_func in steps:
        try:
            results[step_name] = step_func()
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user.")
            break
        except Exception as e:
            print(f"\nFAIL Unexpected error in {step_name}: {e}")
            results[step_name] = False
    
    # Summary
    print(f"\n\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    for step_name, result in results.items():
        status_str = "OK" if result else "FAIL"
        print(f"  {status_str} {step_name}")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFAIL Fatal error: {e}")
        sys.exit(1)
