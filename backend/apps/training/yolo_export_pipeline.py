"""
YOLO Model Export Pipeline for Production Optimization.

Supports exporting .pt models to:
- ONNX (cross-platform compatibility)
- TensorRT (RTX 4090 optimization)
- OpenVINO (Intel optimization)
"""
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple

import torch
import numpy as np
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class YOLOExportPipeline:
    """
    Production-grade YOLO model export pipeline with benchmarking.
    """
    
    SUPPORTED_FORMATS = ["onnx", "tensorrt", "openvino", "torchscript"]
    BENCHMARK_HARDWARE = "RTX 4090"
    DEFAULT_IMG_SIZE = 640
    NUM_WARMUP_RUNS = 50
    NUM_BENCHMARK_RUNS = 100
    
    def __init__(self, pt_model_path: str, output_dir: str = None):
        """
        Initialize export pipeline.
        
        Args:
            pt_model_path: Path to .pt model file
            output_dir: Output directory for exported models
        """
        self.pt_model_path = Path(pt_model_path)
        self.output_dir = Path(output_dir or "backend/models_registry/exports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.pt_model_path.exists():
            raise FileNotFoundError(f"Model file not found: {pt_model_path}")
        
        # Load model
        logger.info(f"Loading YOLO model from {pt_model_path}")
        self.model = YOLO(str(pt_model_path))
        self.model_size_mb = self.pt_model_path.stat().st_size / (1024 * 1024)
        
        logger.info(f"✓ Model loaded successfully (Size: {self.model_size_mb:.2f} MB)")
    
    def export_onnx(self, opset_version: int = 13, use_dynamic_axes: bool = True) -> Dict:
        """
        Export model to ONNX format.
        
        Args:
            opset_version: ONNX opset version
            use_dynamic_axes: Allow dynamic batch size
            
        Returns:
            Export result dictionary
        """
        logger.info("Exporting to ONNX format...")
        start_time = time.time()
        
        try:
            export_path = self.output_dir / f"{self.pt_model_path.stem}.onnx"
            
            exported_model_path = self.model.export(
                format="onnx",
                imgsz=self.DEFAULT_IMG_SIZE,
                half=False,
                opset=opset_version,
                simplify=True,
                dynamic=use_dynamic_axes
            )
            
            export_time = time.time() - start_time
            file_size_mb = Path(exported_model_path).stat().st_size / (1024 * 1024)
            
            logger.info(f"✓ ONNX export completed in {export_time:.2f}s (Size: {file_size_mb:.2f} MB)")
            
            # Benchmark
            benchmark_results = self._benchmark_onnx(str(exported_model_path))
            
            return {
                "status": "completed",
                "format": "onnx",
                "file_path": str(exported_model_path),
                "file_size_mb": file_size_mb,
                "export_time_seconds": export_time,
                "params": {
                    "opset_version": opset_version,
                    "dynamic_axes": use_dynamic_axes,
                    "simplified": True
                },
                "benchmark": benchmark_results,
                "recommendation": "✓ Recommended for cross-platform compatibility"
            }
        except Exception as e:
            logger.error(f"✗ ONNX export failed: {str(e)}")
            return {
                "status": "failed",
                "format": "onnx",
                "error": str(e)
            }
    
    def export_tensorrt(self, half_precision: bool = True, workspace_size_gb: int = 8) -> Dict:
        """
        Export model to TensorRT format (RTX 4090 optimization).
        
        Args:
            half_precision: Use FP16 for speed
            workspace_size_gb: TensorRT workspace size
            
        Returns:
            Export result dictionary
        """
        logger.info("Exporting to TensorRT format (RTX 4090 optimization)...")
        start_time = time.time()
        
        try:
            # Check for CUDA availability
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA is required for TensorRT export")
            
            export_path = self.output_dir / f"{self.pt_model_path.stem}.engine"
            
            exported_model_path = self.model.export(
                format="engine",
                imgsz=self.DEFAULT_IMG_SIZE,
                half=half_precision,
                device=0,
                workspace=workspace_size_gb,
                verbose=False,
                simplify=False
            )
            
            export_time = time.time() - start_time
            file_size_mb = Path(exported_model_path).stat().st_size / (1024 * 1024)
            
            logger.info(f"✓ TensorRT export completed in {export_time:.2f}s (Size: {file_size_mb:.2f} MB)")
            
            # Benchmark
            benchmark_results = self._benchmark_tensorrt(str(exported_model_path))
            
            return {
                "status": "completed",
                "format": "tensorrt",
                "file_path": str(exported_model_path),
                "file_size_mb": file_size_mb,
                "export_time_seconds": export_time,
                "params": {
                    "half_precision": half_precision,
                    "workspace_size_gb": workspace_size_gb,
                    "hardware": "RTX 4090"
                },
                "benchmark": benchmark_results,
                "recommendation": "✓✓✓ BEST for RTX 4090 (fastest inference)"
            }
        except Exception as e:
            logger.error(f"✗ TensorRT export failed: {str(e)}")
            return {
                "status": "failed",
                "format": "tensorrt",
                "error": str(e)
            }
    
    def export_openvino(self) -> Dict:
        """
        Export model to OpenVINO format (Intel optimization).
        
        Returns:
            Export result dictionary
        """
        logger.info("Exporting to OpenVINO format...")
        start_time = time.time()
        
        try:
            exported_model_path = self.model.export(
                format="openvino",
                imgsz=self.DEFAULT_IMG_SIZE,
                half=False
            )
            
            export_time = time.time() - start_time
            file_size_mb = Path(exported_model_path).stat().st_size / (1024 * 1024) if Path(exported_model_path).exists() else 0
            
            logger.info(f"✓ OpenVINO export completed in {export_time:.2f}s")
            
            return {
                "status": "completed",
                "format": "openvino",
                "file_path": str(exported_model_path),
                "file_size_mb": file_size_mb,
                "export_time_seconds": export_time,
                "params": {},
                "recommendation": "Recommended for Intel CPU/VPU deployment"
            }
        except Exception as e:
            logger.error(f"✗ OpenVINO export failed: {str(e)}")
            return {
                "status": "failed",
                "format": "openvino",
                "error": str(e)
            }
    
    def export_torchscript(self) -> Dict:
        """
        Export model to TorchScript format.
        
        Returns:
            Export result dictionary
        """
        logger.info("Exporting to TorchScript format...")
        start_time = time.time()
        
        try:
            exported_model_path = self.model.export(
                format="torchscript",
                imgsz=self.DEFAULT_IMG_SIZE
            )
            
            export_time = time.time() - start_time
            file_size_mb = Path(exported_model_path).stat().st_size / (1024 * 1024)
            
            logger.info(f"✓ TorchScript export completed in {export_time:.2f}s (Size: {file_size_mb:.2f} MB)")
            
            return {
                "status": "completed",
                "format": "torchscript",
                "file_path": str(exported_model_path),
                "file_size_mb": file_size_mb,
                "export_time_seconds": export_time,
                "params": {},
                "recommendation": "Recommended for PyTorch-based applications"
            }
        except Exception as e:
            logger.error(f"✗ TorchScript export failed: {str(e)}")
            return {
                "status": "failed",
                "format": "torchscript",
                "error": str(e)
            }
    
    def _benchmark_onnx(self, onnx_path: str) -> Dict:
        """
        Benchmark ONNX model using ONNX Runtime.
        
        Args:
            onnx_path: Path to exported ONNX model
            
        Returns:
            Benchmark results
        """
        try:
            import onnxruntime as rt
            
            logger.info(f"Benchmarking ONNX model on CPU...")
            
            # Load ONNX model
            sess = rt.InferenceSession(onnx_path)
            input_name = sess.get_inputs()[0].name
            
            # Create dummy input
            dummy_input = np.random.rand(1, 3, self.DEFAULT_IMG_SIZE, self.DEFAULT_IMG_SIZE).astype(np.float32)
            
            # Warmup
            for _ in range(self.NUM_WARMUP_RUNS):
                sess.run(None, {input_name: dummy_input})
            
            # Benchmark
            times = []
            for _ in range(self.NUM_BENCHMARK_RUNS):
                start = time.time()
                sess.run(None, {input_name: dummy_input})
                times.append((time.time() - start) * 1000)  # Convert to ms
            
            times = np.array(times)
            
            return {
                "inference_time_ms": float(np.mean(times)),
                "min_latency_ms": float(np.min(times)),
                "max_latency_ms": float(np.max(times)),
                "p95_latency_ms": float(np.percentile(times, 95)),
                "throughput_fps": float(1000 / np.mean(times)),
                "backend": "ONNX Runtime (CPU)"
            }
        except ImportError:
            logger.warning("ONNX Runtime not installed, skipping benchmark")
            return {"status": "onnx_runtime_not_installed"}
    
    def _benchmark_tensorrt(self, engine_path: str) -> Dict:
        """
        Benchmark TensorRT model on GPU.
        
        Args:
            engine_path: Path to TensorRT engine file
            
        Returns:
            Benchmark results
        """
        try:
            import tensorrt as trt
            
            logger.info(f"Benchmarking TensorRT model on GPU...")
            
            # Load engine
            logger.setLevel(logging.WARNING)
            with open(engine_path, 'rb') as f:
                engine = trt.Runtime(trt.Logger(trt.Logger.WARNING)).deserialize_cuda_engine(f.read())
            
            context = engine.create_execution_context()
            
            # Create CUDA stream
            stream = torch.cuda.Stream()
            
            # Create dummy input
            dummy_input = torch.randn(1, 3, self.DEFAULT_IMG_SIZE, self.DEFAULT_IMG_SIZE, dtype=torch.float32, device='cuda')
            
            # Warmup
            with torch.cuda.stream(stream):
                for _ in range(self.NUM_WARMUP_RUNS):
                    context.execute_async_v2(
                        bindings=[dummy_input.data_ptr(), torch.empty(1, 80, 80, 80).data_ptr()],
                        stream_handle=stream.cuda_stream
                    )
            torch.cuda.synchronize()
            
            # Benchmark
            times = []
            with torch.no_grad():
                with torch.cuda.stream(stream):
                    for _ in range(self.NUM_BENCHMARK_RUNS):
                        torch.cuda.synchronize()
                        start = time.time()
                        context.execute_async_v2(
                            bindings=[dummy_input.data_ptr(), torch.empty(1, 80, 80, 80).data_ptr()],
                            stream_handle=stream.cuda_stream
                        )
                        torch.cuda.synchronize()
                        times.append((time.time() - start) * 1000)
            
            times = np.array(times)
            
            return {
                "inference_time_ms": float(np.mean(times)),
                "min_latency_ms": float(np.min(times)),
                "max_latency_ms": float(np.max(times)),
                "p95_latency_ms": float(np.percentile(times, 95)),
                "throughput_fps": float(1000 / np.mean(times)),
                "backend": "TensorRT (GPU)",
                "hardware": "RTX 4090"
            }
        except ImportError:
            logger.warning("TensorRT not installed, skipping benchmark")
            return {"status": "tensorrt_not_installed"}
        except Exception as e:
            logger.warning(f"TensorRT benchmark failed: {e}")
            return {"status": "benchmark_failed", "error": str(e)}
    
    def export_all(self) -> Dict:
        """
        Export to all supported formats with full benchmarking.
        
        Returns:
            Dictionary with all export results
        """
        logger.info("=" * 80)
        logger.info(f"YOLO MODEL EXPORT PIPELINE")
        logger.info(f"Source Model: {self.pt_model_path.name} ({self.model_size_mb:.2f} MB)")
        logger.info(f"Output Directory: {self.output_dir}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 80)
        
        results = {
            "source_model": str(self.pt_model_path),
            "source_size_mb": self.model_size_mb,
            "output_directory": str(self.output_dir),
            "timestamp": datetime.now().isoformat(),
            "exports": {}
        }
        
        # Export to ONNX
        logger.info("\n[1/4] ONNX Export")
        logger.info("-" * 80)
        results["exports"]["onnx"] = self.export_onnx()
        
        # Export to TensorRT
        logger.info("\n[2/4] TensorRT Export (RTX 4090)")
        logger.info("-" * 80)
        results["exports"]["tensorrt"] = self.export_tensorrt()
        
        # Export to OpenVINO
        logger.info("\n[3/4] OpenVINO Export")
        logger.info("-" * 80)
        results["exports"]["openvino"] = self.export_openvino()
        
        # Export to TorchScript
        logger.info("\n[4/4] TorchScript Export")
        logger.info("-" * 80)
        results["exports"]["torchscript"] = self.export_torchscript()
        
        # Generate recommendations
        logger.info("\n" + "=" * 80)
        logger.info("EXPORT SUMMARY & RECOMMENDATIONS")
        logger.info("=" * 80)
        
        self._print_recommendations(results)
        
        # Save results to JSON
        results_file = self.output_dir / "export_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"\n✓ Export results saved to: {results_file}")
        
        return results
    
    def _print_recommendations(self, results: Dict):
        """Print export recommendations."""
        logger.info("\nFORMAT COMPARISONS:")
        logger.info("-" * 80)
        
        for format_name, result in results["exports"].items():
            if result["status"] == "completed":
                benchmark = result.get("benchmark", {})
                fps = benchmark.get("throughput_fps", 0)
                latency = benchmark.get("inference_time_ms", 0)
                file_size = result["file_size_mb"]
                
                logger.info(f"\n{format_name.upper():<15} | "
                          f"FPS: {fps:>7.1f} | "
                          f"Latency: {latency:>6.2f}ms | "
                          f"Size: {file_size:>6.1f}MB | "
                          f"{result.get('recommendation', '')}")
        
        logger.info("\n" + "-" * 80)
        logger.info("\nRECOMMENDATION FOR PRODUCTION:")
        tensorrt_result = results["exports"].get("tensorrt", {})
        if tensorrt_result["status"] == "completed":
            fps = tensorrt_result["benchmark"].get("throughput_fps", 0)
            latency = tensorrt_result["benchmark"].get("inference_time_ms", 0)
            logger.info(f"\n✓✓✓ USE TENSORRT for RTX 4090 deployment")
            logger.info(f"    Achieves {fps:.1f} FPS with {latency:.2f}ms latency")
            logger.info(f"    Perfect for real-time production inference")
        else:
            logger.info("\n⚠ TensorRT export failed, consider ONNX as fallback")


def export_model(pt_model_path: str, output_dir: str = None, formats: List[str] = None) -> Dict:
    """
    Convenience function to export a model.
    
    Args:
        pt_model_path: Path to .pt model
        output_dir: Output directory
        formats: List of formats to export (None = all)
        
    Returns:
        Export results
    """
    pipeline = YOLOExportPipeline(pt_model_path, output_dir)
    return pipeline.export_all()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python yolo_export_pipeline.py <path_to_model.pt> [output_dir]")
        sys.exit(1)
    
    pt_model = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    
    export_model(pt_model, output)
