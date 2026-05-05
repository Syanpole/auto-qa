"""
AI Inference API Views for Real-Time Defect Detection.
"""
import base64
import logging
from io import BytesIO

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from PIL import Image

from apps.common.permissions import IsQaOperator, IsAdmin, IsSuperAdmin
from apps.audit.services import log_event
from apps.qa.models import DefectEvent, QAStation, ProductProfile
from .services import invoke_inference
from .serializers import DefectEventSerializer

logger = logging.getLogger(__name__)


class InferenceViewSet(viewsets.GenericViewSet):
    """
    Real-time defect detection inference endpoints.
    """
    permission_classes = [IsAuthenticated, IsQaOperator]
    
    @action(detail=False, methods=['post'])
    def realtime_inference(self, request):
        """
        Run real-time inference on a single image.
        
        Request body:
        {
            "image_base64": "base64_encoded_image",
            "station_id": "Station-A",
            "product_id": "IC_001",
            "model_name": "ic_defect_v1",
            "confidence_threshold": 0.85
        }
        """
        try:
            image_base64 = request.data.get('image_base64')
            station_id = request.data.get('station_id')
            product_id = request.data.get('product_id')
            confidence = float(request.data.get('confidence_threshold', 0.85))
            
            if not all([image_base64, station_id, product_id]):
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Decode image
            try:
                image_data = base64.b64decode(image_base64)
                image = Image.open(BytesIO(image_data))
            except Exception as e:
                logger.error(f"Image decode error: {str(e)}")
                return Response(
                    {'error': 'Invalid image data'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Prepare inference payload
            payload = {
                'image_base64': image_base64,
                'station_id': station_id,
                'product_id': product_id,
                'confidence_threshold': confidence,
                'user_id': request.user.id
            }
            
            # Run inference
            result = invoke_inference(payload, request)
            
            # Log inference event
            log_event(
                user=request.user,
                action_type='inference_request',
                target_object=f"{station_id}/{product_id}",
                metadata={
                    'station_id': station_id,
                    'product_id': product_id,
                    'confidence': confidence,
                    'defects_found': result.get('detection_count', 0),
                    'status': result.get('pass_fail_status')
                },
                request=request
            )
            
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Inference error: {str(e)}")
            self.stats["errors"] += 1
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def batch_inference(self, request):
        """
        Batch inference on multiple images.
        
        Request body:
        {
            "images": [
                {"image_base64": "...", "product_id": "IC_001"},
                {"image_base64": "...", "product_id": "IC_002"}
            ],
            "station_id": "Station-A",
            "confidence_threshold": 0.85
        }
        """
        try:
            images = request.data.get('images', [])
            station_id = request.data.get('station_id')
            confidence = float(request.data.get('confidence_threshold', 0.85))
            
            if not images or not station_id:
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            results = []
            for idx, img_data in enumerate(images):
                payload = {
                    'image_base64': img_data.get('image_base64'),
                    'station_id': station_id,
                    'product_id': img_data.get('product_id', f'Unknown_{idx}'),
                    'confidence_threshold': confidence,
                    'user_id': request.user.id,
                    'mode': 'batch'
                }
                
                result = invoke_inference(payload, request)
                results.append(result)
            
            return Response({
                'status': 'completed',
                'total_processed': len(results),
                'results': results
            })
        
        except Exception as e:
            logger.error(f"Batch inference error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def snapshot(self, request):
        """
        Save inference snapshot with metadata.
        """
        try:
            serializer = DefectEventSerializer(data=request.data)
            if serializer.is_valid():
                defect_event = serializer.save(recorded_by=request.user)
                
                log_event(
                    user=request.user,
                    action_type='snapshot_saved',
                    target_object=str(defect_event.id),
                    metadata={
                        'station': defect_event.qa_station.station_code,
                        'product': defect_event.product.product_code,
                        'result': defect_event.result
                    },
                    request=request
                )
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Snapshot error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def disposition(self, request):
        """
        Record QA operator disposition (pass/rework/scrap).
        
        Request body:
        {
            "station_id": "Station-A",
            "product_id": "IC_001",
            "operator_action": "PASS" | "REWORK" | "SCRAP",
            "defects_found": 2,
            "model_used": "ic_defect_v1",
            "override_reason": "Optional reason for override"
        }
        """
        try:
            station_code = request.data.get('station_id')
            product_code = request.data.get('product_id')
            operator_action = request.data.get('operator_action')
            defects_found = request.data.get('defects_found', 0)
            override_reason = request.data.get('override_reason', '')
            
            if not all([station_code, product_code, operator_action]):
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get station and product
            try:
                station = QAStation.objects.get(station_code=station_code)
                product = ProductProfile.objects.get(product_code=product_code)
            except (QAStation.DoesNotExist, ProductProfile.DoesNotExist):
                return Response(
                    {'error': 'Station or product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Map operator action to result
            action_map = {
                'PASS': 'pass',
                'REWORK': 'review',
                'SCRAP': 'fail'
            }
            
            result = action_map.get(operator_action, 'review')
            disposition_map = {
                'PASS': 'acknowledged',
                'REWORK': 'rework',
                'SCRAP': 'waste'
            }
            final_disposition = disposition_map.get(operator_action, 'acknowledged')
            
            # Create defect event record
            defect_event = DefectEvent.objects.create(
                qa_station=station,
                product=product,
                recorded_by=request.user,
                result=result,
                final_disposition=final_disposition,
                operator_action=operator_action,
                reviewed_by=request.user if request.user.groups.filter(name__in=['admin', 'super_admin']).exists() else None,
                reviewed_at=timezone.now() if request.user.groups.filter(name__in=['admin', 'super_admin']).exists() else None,
                override_reason=override_reason,
                defect_count=defects_found
            )
            
            # Log action
            log_event(
                user=request.user,
                action_type=f'disposition_{operator_action.lower()}',
                target_object=str(defect_event.id),
                metadata={
                    'station': station.station_code,
                    'product': product.product_code,
                    'defects': defects_found,
                    'action': operator_action,
                    'override_reason': override_reason
                },
                request=request
            )
            
            return Response({
                'status': 'recorded',
                'defect_event_id': str(defect_event.id),
                'operator': request.user.username,
                'action': operator_action,
                'timestamp': timezone.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Disposition error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=false, methods=['get'])
    def stats(self, request):
        """Get inference statistics."""
        try:
            total_inferences = DefectEvent.objects.filter(
                recorded_by=request.user
            ).count()
            
            pass_count = DefectEvent.objects.filter(
                recorded_by=request.user,
                result='pass'
            ).count()
            
            fail_count = DefectEvent.objects.filter(
                recorded_by=request.user,
                result='fail'
            ).count()
            
            pass_rate = (pass_count / total_inferences * 100) if total_inferences > 0 else 0
            
            return Response({
                'total_inferences': total_inferences,
                'pass_count': pass_count,
                'fail_count': fail_count,
                'pass_rate_percent': pass_rate
            })
        
        except Exception as e:
            logger.error(f"Stats error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
