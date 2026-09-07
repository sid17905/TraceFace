/**
 * Add New Graph Component
 * 
 * Upload an image to create a new provenance graph.
 */

import React, { useState, useRef } from 'react';
import { TraceFaceApi } from '../../services/api';
import type { ScanResponse, StageEvent, PropagationGraph } from '../../types';

interface AddNewGraphProps {
  onGraphCreated: (graph: PropagationGraph, jobId: string) => void;
}

export const AddNewGraph: React.FC<AddNewGraphProps> = ({ onGraphCreated }) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [events, setEvents] = useState<StageEvent[]>([]);
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select an image file');
      return;
    }

    setUploading(true);
    setEvents([]);
    setResult(null);
    setError(null);

    try {
      // Upload and scan the image
      const scanResponse = await TraceFaceApi.uploadScan(file, true);
      setResult(scanResponse);

      // Stream events from the pipeline
      TraceFaceApi.streamScanEvents(
        scanResponse.job_id,
        (event) => {
          setEvents((prev) => [...prev, event]);
        },
        async () => {
          // On complete, load the graph
          try {
            const graphData = await TraceFaceApi.getJobGraph(scanResponse.job_id);
            onGraphCreated(graphData.graph, scanResponse.job_id);
          } catch (err) {
            console.error('Failed to load graph:', err);
          }
          setUploading(false);
        },
        (err) => {
          console.error('Stream error:', err);
          setError('Pipeline streaming error');
          setUploading(false);
        }
      );
    } catch (err: any) {
      setError(err.message || 'Upload failed');
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith('image/')) {
      setFile(droppedFile);
      setError(null);
    }
  };

  const stages = [
    'face_extraction',
    'liveness_gate',
    'osint_crawl',
    'biometric_gate',
    'merkle_seal',
    'ipfs_pin',
    'blockchain_anchor',
  ];

  const getStageStatus = (stageName: string) => {
    const stageEvents = events.filter((e) => e.stage === stageName);
    if (stageEvents.length === 0) return 'pending';
    if (stageEvents.some((e) => e.status === 'error')) return 'error';
    if (stageEvents.some((e) => e.status === 'done')) return 'done';
    return 'running';
  };

  const getStageIcon = (status: string) => {
    switch (status) {
      case 'done':
        return '✅';
      case 'error':
        return '❌';
      case 'running':
        return '⏳';
      default:
        return '⏸️';
    }
  };

  return (
    <div className="add-new-graph">
      <h2>➕ Create New Provenance Graph</h2>

      <div
        className="upload-zone"
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        
        {file ? (
          <div className="preview">
            <img src={URL.createObjectURL(file)} alt="Preview" />
            <p>{file.name}</p>
          </div>
        ) : (
          <div className="placeholder">
            <p>📁 Drop an image here or click to upload</p>
            <p className="hint">Accepts: JPG, PNG, WebP (max 15MB)</p>
          </div>
        )}
      </div>

      {error && <div className="error-message">❌ {error}</div>}

      <button
        className="upload-btn"
        onClick={handleUpload}
        disabled={!file || uploading}
      >
        {uploading ? '⏳ Processing...' : '🔍 Scan & Create Graph'}
      </button>

      {events.length > 0 && (
        <div className="pipeline-progress">
          <h3>Pipeline Progress</h3>
          <div className="stages">
            {stages.map((stage) => {
              const status = getStageStatus(stage);
              return (
                <div key={stage} className={`stage ${status}`}>
                  <span className="icon">{getStageIcon(status)}</span>
                  <span className="name">{stage.replace('_', ' ')}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {result && (
        <div className="result">
          <h3>✅ Scan Complete!</h3>
          <div className="result-details">
            <div className="detail">
              <span className="label">Job ID:</span>
              <span className="value">{result.job_id}</span>
            </div>
            <div className="detail">
              <span className="label">Scan ID:</span>
              <span className="value">{result.scan.scan_id}</span>
            </div>
            <div className="detail">
              <span className="label">Similarity:</span>
              <span className="value">
                {result.scan.quality_metrics?.confidence_score?.toFixed(3) || 'N/A'}
              </span>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .add-new-graph {
          padding: 1.5rem;
          background: #1a1a1a;
          border-radius: 8px;
          color: #fff;
        }
        h2 {
          margin: 0 0 1rem 0;
        }
        .upload-zone {
          border: 2px dashed #4b5563;
          border-radius: 8px;
          padding: 3rem;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s;
          margin-bottom: 1rem;
        }
        .upload-zone:hover {
          border-color: #3b82f6;
          background: #1e1e1e;
        }
        .preview img {
          max-width: 200px;
          max-height: 200px;
          border-radius: 8px;
          margin-bottom: 0.5rem;
        }
        .preview p {
          margin: 0;
          color: #9ca3af;
          font-size: 0.85rem;
        }
        .placeholder p {
          margin: 0.5rem 0;
        }
        .hint {
          color: #6b7280;
          font-size: 0.85rem;
        }
        .upload-btn {
          width: 100%;
          padding: 1rem;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 6px;
          font-size: 1rem;
          font-weight: bold;
          cursor: pointer;
          transition: background 0.2s;
        }
        .upload-btn:hover:not(:disabled) {
          background: #2563eb;
        }
        .upload-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .error-message {
          margin: 1rem 0;
          padding: 1rem;
          background: #7f1d1d;
          border-radius: 6px;
          color: #fca5a5;
        }
        .pipeline-progress {
          margin-top: 1.5rem;
        }
        .stages {
          display: grid;
          gap: 0.5rem;
        }
        .stage {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem;
          background: #2a2a2a;
          border-radius: 4px;
        }
        .stage.done {
          background: #064e3b;
        }
        .stage.error {
          background: #7f1d1d;
        }
        .stage.running {
          background: #78350f;
        }
        .icon {
          font-size: 1.25rem;
        }
        .name {
          text-transform: capitalize;
        }
        .result {
          margin-top: 1.5rem;
          padding: 1rem;
          background: #064e3b;
          border-radius: 6px;
        }
        .result-details {
          display: grid;
          gap: 0.5rem;
          margin-top: 0.5rem;
        }
        .result .detail {
          display: flex;
          justify-content: space-between;
        }
        .result .label {
          color: #9ca3af;
        }
        .result .value {
          font-family: monospace;
        }
      `}</style>
    </div>
  );
};

export default AddNewGraph;
