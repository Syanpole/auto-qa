import React, { useEffect, useRef, useState } from 'react';
import { AlertCircle, CheckCircle, XCircle, Download, Settings } from 'lucide-react';

interface DetectionResult {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
}

interface InferenceResponse {
  status: string;
  pass_fail_status?: string;
  verdict?: string;
  detections?: DetectionResult[];
  defects?: Array<{ defect_class: string; confidence: number; bbox: [number, number, number, number] }>;
  detection_count?: number;
  inference_time_ms?: number;
  latency_ms?: number;
  model_used?: string;
  timestamp?: string;
}

interface QAInspectionLog {
  id: string;
  timestamp: string;
  product_id: string;
  model_used: string;
  result: string;
  defects_found: number;
  image_path: string;
  operator_action?: string;
}

export default function RealTimeDetectionPage() {
  // State management
  const [cameraActive, setCameraActive] = useState(false);
  const [selectedStation, setSelectedStation] = useState('Station-A');
  const [selectedProduct, setSelectedProduct] = useState('IC_001');
  const [selectedModel, setSelectedModel] = useState('ic_defect_v1');
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.85);
  const [liveInference, setLiveInference] = useState<InferenceResponse | null>(null);
  const [detectionCount, setDetectionCount] = useState(0);
  const [operatorAction, setOperatorAction] = useState<string | null>(null);
  const [inspectionLog, setInspectionLog] = useState<QAInspectionLog[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [inferenceRate, setInferenceRate] = useState('1.0'); // fps

  // Refs
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const inferenceTimerRef = useRef<number | null>(null);

  // Station and product data
  const stations = ['Station-A', 'Station-B', 'Station-C'];
  const products = ['IC_001', 'IC_002', 'IC_003'];
  const models = ['ic_defect_v1', 'ic_defect_v2_optimized', 'rt_detr_ic'];
  // Initialize camera
  useEffect(() => {
    const initCamera = async () => {
      try {
        if (cameraActive) {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: {
              width: { ideal: 1280 },
              height: { ideal: 720 },
              facingMode: 'environment'
            }
          });

          streamRef.current = stream;
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }

          // Start inference loop
          startInferenceLoop();
        } else {
          stopCamera();
        }
      } catch (error) {
        console.error('Camera access error:', error);
        alert('Unable to access camera. Please check permissions.');
      }
    };

    initCamera();

    return () => {
      stopCamera();
    };
  }, [cameraActive]);

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (inferenceTimerRef.current) {
      clearInterval(inferenceTimerRef.current);
    }
  };

  const startInferenceLoop = () => {
    const fps = parseFloat(inferenceRate);
    const interval = fps > 0 ? 1000 / fps : 1000;

    inferenceTimerRef.current = setInterval(async () => {
      if (videoRef.current && videoRef.current.readyState === videoRef.current.HAVE_ENOUGH_DATA) {
        await captureAndInfer();
      }
    }, interval);
  };

  const captureAndInfer = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    try {
      const ctx = canvasRef.current.getContext('2d');
      if (!ctx) return;

      // Draw video frame to canvas
      ctx.drawImage(videoRef.current, 0, 0, canvasRef.current.width, canvasRef.current.height);

      // Get image data as base64
      const imageBase64 = canvasRef.current.toDataURL('image/jpeg').split(',')[1];

      // Call inference API
      const response = await fetch('/api/v1/ai/infer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_base64: imageBase64,
          station_id: selectedStation,
          product_id: selectedProduct,
          model_name: selectedModel,
          confidence_threshold: confidenceThreshold
        })
      });

      if (response.ok) {
        const result: InferenceResponse = await response.json();
        const normalizedDetections: DetectionResult[] = result.detections ??
          (result.defects || []).map((d, idx) => ({
            class_id: idx,
            class_name: d.defect_class,
            confidence: d.confidence,
            bbox: d.bbox,
          }));

        const normalizedStatus = result.pass_fail_status ||
          (result.verdict?.toLowerCase() === 'pass' ? 'PASS' : 'REJECT');

        const normalizedResult: InferenceResponse = {
          ...result,
          pass_fail_status: normalizedStatus,
          detections: normalizedDetections,
          detection_count: result.detection_count ?? normalizedDetections.length,
          inference_time_ms: result.inference_time_ms ?? result.latency_ms ?? 0,
          timestamp: result.timestamp ?? new Date().toISOString(),
        };

        setLiveInference(normalizedResult);
        setDetectionCount(normalizedResult.detection_count || 0);
        
        // Draw bounding boxes
        drawDetections(normalizedResult.detections || []);
      }
    } catch (error) {
      console.error('Inference error:', error);
    }
  };

  const drawDetections = (detections: DetectionResult[]) => {
    if (!canvasRef.current || !videoRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear previous drawings
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    // Draw bounding boxes
    detections.forEach((detection, index) => {
      const [x1, y1, x2, y2] = detection.bbox;
      const width = x2 - x1;
      const height = y2 - y1;

      // Color based on defect type
      const colors: Record<string, string> = {
        scratch: '#FF6B6B',
        crack: '#FF4444',
        chip: '#FFA500',
        surface_defect: '#FFD700'
      };
      const color = colors[detection.class_name] || '#FF6B6B';

      // Draw rectangle
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.strokeRect(x1, y1, width, height);

      // Draw label
      const label = `${detection.class_name} ${(detection.confidence * 100).toFixed(1)}%`;
      ctx.fillStyle = color;
      ctx.font = 'bold 14px Arial';
      ctx.fillText(label, x1, y1 - 10);
    });
  };

  const handleCapture = async () => {
    if (!canvasRef.current) return;

    try {
      const timestamp = new Date().toISOString();
      const imagePath = `/snapshots/${selectedStation}_${timestamp}.jpg`;

      const newLog: QAInspectionLog = {
        id: `${Date.now()}`,
        timestamp,
        product_id: selectedProduct,
        model_used: selectedModel,
        result: liveInference?.pass_fail_status || 'UNKNOWN',
        defects_found: liveInference?.detection_count || 0,
        image_path: imagePath
      };

      setInspectionLog([newLog, ...inspectionLog.slice(0, 49)]);

      // Save snapshot
      canvasRef.current.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${selectedStation}_${timestamp}.jpg`;
          a.click();
          URL.revokeObjectURL(url);
        }
      }, 'image/jpeg');

      // Log to backend
      await fetch('/api/v1/ai/snapshot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newLog,
          station_id: selectedStation,
          product_id: selectedProduct,
          result: liveInference?.pass_fail_status || 'REVIEW',
        })
      });
    } catch (error) {
      console.error('Capture error:', error);
    }
  };

  const handleDisposition = async (action: string) => {
    setOperatorAction(action);

    try {
      await fetch('/api/v1/ai/disposition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inspection_id: `${Date.now()}`,
          station_id: selectedStation,
          product_id: selectedProduct,
          operator_action: action,
          defects_found: detectionCount,
          model_used: selectedModel,
          timestamp: new Date().toISOString()
        })
      });

      setTimeout(() => setOperatorAction(null), 2000);
    } catch (error) {
      console.error('Disposition error:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PASS':
        return 'text-green-600';
      case 'REJECT':
        return 'text-red-600';
      default:
        return 'text-yellow-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PASS':
        return <CheckCircle className="w-8 h-8" />;
      case 'REJECT':
        return <XCircle className="w-8 h-8" />;
      default:
        return <AlertCircle className="w-8 h-8" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">🔍 Real-Time Defect Detection</h1>
              <p className="text-gray-400">IC Defect Detection - Professional QA Inspection</p>
            </div>
            <button
              onClick={() => setShowSettings(!showSettings)}
              aria-label="Toggle detection settings"
              title="Toggle detection settings"
              className="p-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-white transition"
            >
              <Settings className="w-6 h-6" />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Detection Area */}
          <div className="lg:col-span-2">
            <div className="bg-slate-800 rounded-xl overflow-hidden shadow-2xl border border-slate-700">
              {/* Video Canvas */}
              <div className="relative bg-black aspect-video">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  className="w-full h-full object-cover hidden"
                />
                <canvas
                  ref={canvasRef}
                  width={1280}
                  height={720}
                  className="w-full h-full object-cover"
                />
                
                {!cameraActive && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/80 backdrop-blur-sm">
                    <div className="text-center">
                      <p className="text-gray-400 mb-4">Camera not active</p>
                      <button
                        onClick={() => setCameraActive(true)}
                        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
                      >
                        Start Camera
                      </button>
                    </div>
                  </div>
                )}

                {/* Live Status Badge */}
                {cameraActive && (
                  <div className="absolute top-4 left-4 bg-green-500 text-white px-3 py-1 rounded-full flex items-center gap-2 text-sm font-medium">
                    <span className="animate-pulse">●</span>
                    LIVE
                  </div>
                )}

                {/* Inference Time */}
                {liveInference && liveInference.inference_time_ms !== undefined && (
                  <div className="absolute bottom-4 right-4 bg-black/70 text-gray-200 px-3 py-2 rounded-lg text-sm font-mono">
                    {liveInference.inference_time_ms.toFixed(1)}ms
                  </div>
                )}
              </div>

              {/* Results Summary */}
              {liveInference && (
                <div className="bg-slate-700/50 border-t border-slate-600 p-4">
                  <div className="flex items-center justify-between">
                    <div className={`flex items-center gap-3 ${getStatusColor(liveInference.pass_fail_status || 'UNKNOWN')}`}>
                      {getStatusIcon(liveInference.pass_fail_status || 'UNKNOWN')}
                      <div>
                        <p className="text-sm font-semibold">Status: {liveInference.pass_fail_status || 'UNKNOWN'}</p>
                        <p className="text-xs text-gray-300">{liveInference.timestamp}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-white">{detectionCount}</p>
                      <p className="text-xs text-gray-400">Defects Found</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Control Buttons */}
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => setCameraActive(!cameraActive)}
                className={`flex-1 py-3 rounded-lg font-medium transition ${
                  cameraActive
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {cameraActive ? 'Stop Camera' : 'Start Camera'}
              </button>
              <button
                onClick={handleCapture}
                disabled={!cameraActive}
                className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Download className="w-4 h-4" />
                Capture Snapshot
              </button>
            </div>
          </div>

          {/* Control Panel & History */}
          <div className="flex flex-col gap-4">
            {/* Configuration Panel */}
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <h2 className="text-lg font-semibold text-white mb-4">Configuration</h2>

              <div className="space-y-4">
                {/* Station Selection */}
                <div>
                  <label htmlFor="qa-station" className="text-sm text-gray-300 block mb-2">QA Station</label>
                  <select
                    id="qa-station"
                    title="QA Station"
                    value={selectedStation}
                    onChange={(e) => setSelectedStation(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 outline-none transition"
                  >
                    {stations.map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>

                {/* Product Selection */}
                <div>
                  <label htmlFor="product-id" className="text-sm text-gray-300 block mb-2">Product</label>
                  <select
                    id="product-id"
                    title="Product"
                    value={selectedProduct}
                    onChange={(e) => setSelectedProduct(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 outline-none transition"
                  >
                    {products.map(p => <option key={p}>{p}</option>)}
                  </select>
                </div>

                {/* Model Selection */}
                <div>
                  <label htmlFor="ai-model" className="text-sm text-gray-300 block mb-2">AI Model</label>
                  <select
                    id="ai-model"
                    title="AI Model"
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 outline-none transition"
                  >
                    {models.map(m => <option key={m}>{m}</option>)}
                  </select>
                </div>

                {/* Confidence Threshold */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label htmlFor="confidence-threshold" className="text-sm text-gray-300">Confidence Threshold</label>
                    <span className="text-sm font-mono text-blue-400">{(confidenceThreshold * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    id="confidence-threshold"
                    title="Confidence Threshold"
                    type="range"
                    min="0.5"
                    max="0.99"
                    step="0.01"
                    value={confidenceThreshold}
                    onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>

                {/* Inference Rate */}
                <div>
                  <label htmlFor="inference-rate" className="text-sm text-gray-300 block mb-2">Inference Rate (FPS)</label>
                  <input
                    id="inference-rate"
                    title="Inference Rate (FPS)"
                    type="number"
                    min="0.1"
                    max="30"
                    step="0.5"
                    value={inferenceRate}
                    onChange={(e) => setInferenceRate(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 outline-none transition"
                  />
                </div>
              </div>
            </div>

            {/* Disposition Buttons */}
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <h2 className="text-lg font-semibold text-white mb-4">Disposition</h2>
              <div className="space-y-2">
                <button
                  onClick={() => handleDisposition('PASS')}
                  className={`w-full py-2 rounded-lg font-medium transition ${
                    operatorAction === 'PASS'
                      ? 'bg-green-600 text-white'
                      : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                  }`}
                >
                  ✓ Accept (Pass)
                </button>
                <button
                  onClick={() => handleDisposition('REWORK')}
                  className={`w-full py-2 rounded-lg font-medium transition ${
                    operatorAction === 'REWORK'
                      ? 'bg-yellow-600 text-white'
                      : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                  }`}
                >
                  🔧 Rework
                </button>
                <button
                  onClick={() => handleDisposition('SCRAP')}
                  className={`w-full py-2 rounded-lg font-medium transition ${
                    operatorAction === 'SCRAP'
                      ? 'bg-red-600 text-white'
                      : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                  }`}
                >
                  ✕ Scrap/Waste
                </button>
              </div>
            </div>

            {/* Inspection History */}
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex-1 overflow-hidden flex flex-col">
              <h2 className="text-lg font-semibold text-white mb-3">Recent Inspections</h2>
              <div className="space-y-2 overflow-y-auto flex-1">
                {inspectionLog.length === 0 ? (
                  <p className="text-gray-400 text-center py-8">No inspections yet</p>
                ) : (
                  inspectionLog.map(log => (
                    <div key={log.id} className="bg-slate-700/50 p-2 rounded text-sm">
                      <div className="flex justify-between items-start mb-1">
                        <span className={`font-semibold ${
                          log.result === 'PASS' ? 'text-green-400' :
                          log.result === 'REJECT' ? 'text-red-400' :
                          'text-yellow-400'
                        }`}>
                          {log.result}
                        </span>
                        <span className="text-gray-400 text-xs">{log.defects_found} defects</span>
                      </div>
                      <p className="text-gray-400 text-xs">{log.product_id}</p>
                      <p className="text-gray-500 text-xs">{new Date(log.timestamp).toLocaleTimeString()}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
