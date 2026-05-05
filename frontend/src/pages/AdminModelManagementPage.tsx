import React, { useEffect, useState } from 'react';
import {
  Upload, Download, Trash2, Eye, Settings, Check, AlertCircle, 
  Clock, Zap, HardDrive, Activity, TrendingUp
} from 'lucide-react';

interface AIModel {
  model_uuid: string;
  model_name: string;
  version_tag: string;
  framework: string;
  status: string;
  is_active: boolean;
  model_size_mb: number;
  throughput_fps: number;
  inference_time_ms: number;
  metrics_json: Record<string, any>;
  deployed_at?: string;
  training_completed_at?: string;
}

interface ModelExport {
  id: string;
  ai_model_id: string;
  export_format: string;
  status: string;
  file_size_mb: number;
  throughput_fps: number;
  inference_time_ms: number;
  completed_at?: string;
}

interface Deployment {
  id: string;
  model_id: string;
  deployment_target: string;
  status: string;
  inference_requests_count: number;
  error_count: number;
  deployed_at: string;
}

interface ModelBenchmark {
  id: string;
  model_id: string;
  hardware: string;
  inference_time_ms: number;
  throughput_fps: number;
  memory_usage_mb: number;
}

export default function AdminModelManagementPage() {
  const [models, setModels] = useState<AIModel[]>([]);
  const [exports, setExports] = useState<ModelExport[]>([]);
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [benchmarks, setBenchmarks] = useState<ModelBenchmark[]>([]);
  
  const [selectedModel, setSelectedModel] = useState<AIModel | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [exportProgress, setExportProgress] = useState(0);
  const [activeTab, setActiveTab] = useState<'models' | 'exports' | 'deployments' | 'benchmarks'>('models');

  // Fetch models
  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await fetch('/api/v1/training/ai-models/');
      if (response.ok) {
        const data = await response.json();
        setModels(data.results || data);
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const handleUploadModel = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    try {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          setUploadProgress((event.loaded / event.total) * 100);
        }
      });

      xhr.addEventListener('load', () => {
        setUploadProgress(0);
        setShowUploadModal(false);
        fetchModels();
      });

      xhr.open('POST', '/api/v1/training/ai-models/upload/');
      xhr.send(formData);
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadProgress(0);
    }
  };

  const handleExportModel = async (modelId: string, format: string) => {
    try {
      const response = await fetch('/api/v1/training/exports/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ai_model_id: modelId,
          export_format: format
        })
      });

      if (response.ok) {
        setExportProgress(100);
        setTimeout(() => setExportProgress(0), 2000);
        // Fetch updated exports
      }
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const handleActivateModel = async (modelId: string) => {
    try {
      const response = await fetch(`/api/v1/training/ai-models/${modelId}/activate/`, {
        method: 'POST'
      });

      if (response.ok) {
        fetchModels();
      }
    } catch (error) {
      console.error('Activation failed:', error);
    }
  };

  const handleDeployModel = async (modelId: string, target: string) => {
    try {
      const response = await fetch('/api/v1/training/deployments/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ai_model_id: modelId,
          deployment_target: target
        })
      });

      if (response.ok) {
        setShowDeployModal(false);
        // Fetch updated deployments
      }
    } catch (error) {
      console.error('Deployment failed:', error);
    }
  };

  const handleDeleteModel = async (modelId: string) => {
    if (!window.confirm('Are you sure? This action cannot be undone.')) return;

    try {
      const response = await fetch(`/api/v1/training/ai-models/${modelId}/`, {
        method: 'DELETE'
      });

      if (response.ok) {
        fetchModels();
      }
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'production':
        return 'bg-green-500/20 text-green-400';
      case 'validated':
        return 'bg-blue-500/20 text-blue-400';
      case 'draft':
        return 'bg-yellow-500/20 text-yellow-400';
      case 'deprecated':
        return 'bg-red-500/20 text-red-400';
      default:
        return 'bg-gray-500/20 text-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">🤖 Model Management</h1>
              <p className="text-gray-400">Manage YOLO models, exports, and deployments</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowUploadModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
              >
                <Upload className="w-4 h-4" />
                Upload Model
              </button>
              <button
                onClick={() => setActiveTab('benchmarks')}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition"
              >
                <Zap className="w-4 h-4" />
                Benchmarks
              </button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6 border-b border-slate-700">
          {(['models', 'exports', 'deployments', 'benchmarks'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-3 px-4 font-medium transition border-b-2 ${
                activeTab === tab
                  ? 'text-blue-400 border-blue-400'
                  : 'text-gray-400 hover:text-gray-300 border-transparent'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Models Tab */}
        {activeTab === 'models' && (
          <div className="space-y-4">
            {models.length === 0 ? (
              <div className="bg-slate-800 rounded-xl p-8 text-center border border-slate-700">
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-400 mb-4">No models uploaded yet</p>
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
                >
                  Upload Your First Model
                </button>
              </div>
            ) : (
              models.map(model => (
                <div
                  key={model.model_uuid}
                  onClick={() => setSelectedModel(model)}
                  className="bg-slate-800 rounded-xl p-6 border border-slate-700 hover:border-slate-600 cursor-pointer transition"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="flex items-center gap-3">
                        <h3 className="text-xl font-bold text-white">{model.model_name}</h3>
                        <span className={`px-2 py-1 rounded text-sm font-medium ${getStatusColor(model.status)}`}>
                          {model.status}
                        </span>
                        {model.is_active && (
                          <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-sm font-medium">
                            ✓ Active
                          </span>
                        )}
                      </div>
                      <p className="text-gray-400 mt-1">v{model.version_tag} • {model.framework}</p>
                    </div>
                    <div className="flex gap-2">
                      {!model.is_active && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleActivateModel(model.model_uuid);
                          }}
                          className="p-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition"
                          title="Activate"
                        >
                          <Check className="w-5 h-5" />
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowExportModal(true);
                          setSelectedModel(model);
                        }}
                        className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                        title="Export"
                      >
                        <Download className="w-5 h-5" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDeployModal(true);
                          setSelectedModel(model);
                        }}
                        className="p-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition"
                        title="Deploy"
                      >
                        <Activity className="w-5 h-5" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteModel(model.model_uuid);
                        }}
                        className="p-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition"
                        title="Delete"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>

                  {/* Model Details Grid */}
                  <div className="grid grid-cols-4 gap-4 pt-4 border-t border-slate-700">
                    <div>
                      <p className="text-sm text-gray-400 mb-1">Model Size</p>
                      <p className="flex items-center gap-2 text-white">
                        <HardDrive className="w-4 h-4" />
                        {model.model_size_mb.toFixed(1)} MB
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-400 mb-1">Throughput</p>
                      <p className="flex items-center gap-2 text-white">
                        <TrendingUp className="w-4 h-4" />
                        {model.throughput_fps.toFixed(1)} FPS
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-400 mb-1">Latency</p>
                      <p className="flex items-center gap-2 text-white">
                        <Clock className="w-4 h-4" />
                        {model.inference_time_ms.toFixed(2)} ms
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-400 mb-1">Accuracy</p>
                      <p className="text-white font-mono">
                        {(model.metrics_json?.accuracy || 0.0).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Exports Tab */}
        {activeTab === 'exports' && (
          <div className="space-y-4">
            {exports.length === 0 ? (
              <div className="bg-slate-800 rounded-xl p-8 text-center border border-slate-700">
                <Download className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-400">No exports yet</p>
              </div>
            ) : (
              exports.map(exp => (
                <div key={exp.id} className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-white font-medium">{exp.export_format.toUpperCase()}</p>
                      <p className="text-sm text-gray-400">{exp.file_size_mb.toFixed(1)} MB • {exp.throughput_fps.toFixed(1)} FPS</p>
                    </div>
                    <span className={`px-3 py-1 rounded text-sm font-medium ${
                      exp.status === 'completed'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {exp.status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Deployments Tab */}
        {activeTab === 'deployments' && (
          <div className="space-y-4">
            {deployments.length === 0 ? (
              <div className="bg-slate-800 rounded-xl p-8 text-center border border-slate-700">
                <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-400">No deployments yet</p>
              </div>
            ) : (
              deployments.map(dep => (
                <div key={dep.id} className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="text-white font-medium">{dep.deployment_target}</p>
                      <p className="text-sm text-gray-400">{new Date(dep.deployed_at).toLocaleDateString()}</p>
                    </div>
                    <span className={`px-3 py-1 rounded text-sm font-medium ${
                      dep.status === 'active'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-gray-500/20 text-gray-400'
                    }`}>
                      {dep.status}
                    </span>
                  </div>
                  <div className="flex gap-4 text-sm text-gray-400">
                    <span>Requests: {dep.inference_requests_count}</span>
                    <span>Errors: {dep.error_count}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Benchmarks Tab */}
        {activeTab === 'benchmarks' && (
          <div className="space-y-4">
            {benchmarks.length === 0 ? (
              <div className="bg-slate-800 rounded-xl p-8 text-center border border-slate-700">
                <Zap className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-400">No benchmarks available</p>
              </div>
            ) : (
              benchmarks.map(bench => (
                <div key={bench.id} className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-white font-medium">{bench.hardware}</p>
                  </div>
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-gray-400">Latency</p>
                      <p className="text-white font-mono">{bench.inference_time_ms.toFixed(2)} ms</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-400">Throughput</p>
                      <p className="text-white font-mono">{bench.throughput_fps.toFixed(1)} FPS</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-400">Memory</p>
                      <p className="text-white font-mono">{bench.memory_usage_mb.toFixed(0)} MB</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-white mb-4">Upload Model</h2>
            <form onSubmit={handleUploadModel} className="space-y-4">
              <label htmlFor="model-file" className="text-sm text-gray-300 block">Model File</label>
              <input
                id="model-file"
                title="Model File"
                type="file"
                name="file"
                accept=".pt,.onnx,.engine"
                required
                className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600"
              />
              <label htmlFor="model-name" className="text-sm text-gray-300 block">Model Name</label>
              <input
                id="model-name"
                title="Model Name"
                type="text"
                name="model_name"
                placeholder="Model name"
                required
                className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600"
              />
              <label htmlFor="version-tag" className="text-sm text-gray-300 block">Version Tag</label>
              <input
                id="version-tag"
                title="Version Tag"
                type="text"
                name="version_tag"
                placeholder="Version (e.g., 1.0.0)"
                required
                className="w-full px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600"
              />
              {uploadProgress > 0 && (
                <progress
                  className="w-full h-2 rounded"
                  max={100}
                  value={uploadProgress}
                  aria-label="Upload progress"
                />
              )}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                >
                  Upload
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
