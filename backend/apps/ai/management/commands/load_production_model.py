"""
Django management command to initialize and load the production YOLO model.
"""
import requests
import logging
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.ai.model_loader import ModelLoaderService
from apps.ai.model_registry import get_registry
from apps.audit.services import log_event

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Load and register the production YOLO model for defect detection"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model-path',
            type=str,
            default=None,
            help='Path to .pt model file (overrides default)'
        )
        parser.add_argument(
            '--model-name',
            type=str,
            default='ic_defect_v1',
            help='Name to register model as'
        )
        parser.add_argument(
            '--confidence-threshold',
            type=float,
            default=0.85,
            help='Confidence threshold for detections'
        )
        parser.add_argument(
            '--iou-threshold',
            type=float,
            default=0.50,
            help='IOU threshold for NMS'
        )
        parser.add_argument(
            '--set-active',
            action='store_true',
            default=True,
            help='Set as active model (default: True)'
        )
    
    def handle(self, *args, **options):
        model_path = options['model_path'] or Path(
            settings.BASE_DIR
        ) / "models_registry" / "deployed_models" / "tpcyolov26nv21gs.pt"
        
        model_name = options['model_name']
        confidence_threshold = options['confidence_threshold']
        iou_threshold = options['iou_threshold']
        set_active = options['set_active']
        
        # Validate file exists
        if not Path(model_path).exists():
            self.stdout.write(
                self.style.ERROR(f"Model file not found: {model_path}")
            )
            return
        
        self.stdout.write(f"Loading model from: {model_path}")
        
        ml_service_url = getattr(settings, 'ML_SERVICE_URL', 'http://localhost:8001')
        
        # Step 1: Load model in ML service
        try:
            load_response = requests.post(
                f"{ml_service_url}/v1/models/load",
                params={
                    "model_path": str(model_path),
                    "model_name": model_name
                },
                timeout=60
            )
            load_response.raise_for_status()
            load_result = load_response.json()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Model loaded in ML service: {load_result.get('status')}"
                )
            )
        except requests.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to load model in ML service: {str(e)}")
            )
            return
        
        # Step 2: Register in backend database and cache
        try:
            result = ModelLoaderService.load_model_from_file(
                file_path=str(model_path),
                model_name=model_name,
                description="Production YOLO model for IC defect detection",
                confidence_threshold=confidence_threshold,
                iou_threshold=iou_threshold,
                version="2.6n",
                architecture="YOLOv8n",
                is_active=set_active
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Model registered in backend: {model_name}"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to register model in backend: {str(e)}")
            )
            return
        
        # Step 3: Activate model
        if set_active:
            try:
                ModelLoaderService.activate_model(model_name)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Model activated as production model")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to activate model: {str(e)}")
                )
                return
        
        # Step 4: Verify model is accessible
        try:
            verify_response = requests.get(
                f"{ml_service_url}/models/{model_name}",
                timeout=10
            )
            verify_response.raise_for_status()
            model_info = verify_response.json()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Model verified in ML service: {model_info.get('model_name')}"
                )
            )
            self.stdout.write(f"  Classes: {len(model_info.get('class_names', []))} detected")
            self.stdout.write(f"  Device: {model_info.get('device')}")
        except requests.RequestException as e:
            self.stdout.write(
                self.style.WARNING(f"Could not verify model: {str(e)}")
            )
        
        # Summary
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("MODEL LOADED SUCCESSFULLY"))
        self.stdout.write("="*70)
        self.stdout.write(f"Model Name: {model_name}")
        self.stdout.write(f"Model Path: {model_path}")
        self.stdout.write(f"Active: {set_active}")
        self.stdout.write(f"Confidence Threshold: {confidence_threshold}")
        self.stdout.write(f"IOU Threshold: {iou_threshold}")
        self.stdout.write("="*70 + "\n")

