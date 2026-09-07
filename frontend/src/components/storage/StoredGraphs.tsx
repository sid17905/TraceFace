/**
 * Stored Graphs Browser
 * 
 * View and load previously stored provenance graphs from the database.
 */

import React, { useEffect, useState } from 'react';
import { TraceFaceApi } from '../../services/api';
import type { PropagationGraph, OriginNode } from '../../types';

interface StoredGraphsProps {
  onGraphSelect: (graph: PropagationGraph, jobId: string) => void;
}

interface GraphJob {
  job_id: string;
  status: string;
  created_at: string;
  nodes_count: number;
  edges_count: number;
}

export const StoredGraphs: React.FC<StoredGraphsProps> = ({ onGraphSelect }) => {
  const [jobs, setJobs] = useState<GraphJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStoredJobs();
  }, []);

  const loadStoredJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      // This would be a new endpoint - let's add it
      const response = await fetch('/api/v1/graph/jobs');
      if (!response.ok) throw new Error('Failed to load stored graphs');
      const data = await response.json();
      setJobs(data.jobs || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load stored graphs');
    } finally {
      setLoading(false);
    }
  };

  const loadGraph = async (jobId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await TraceFaceApi.getJobGraph(jobId);
      setSelectedJob(jobId);
      onGraphSelect(data.graph, jobId);
    } catch (err: any) {
      setError(err.message || 'Failed to load graph');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="stored-graphs">
      <div className="header">
        <h2>💾 Stored Provenance Graphs</h2>
        <button onClick={loadStoredJobs} className="refresh-btn">
          🔄 Refresh
        </button>
      </div>

      {loading && <div className="loading">Loading...</div>}
      {error && <div className="error">❌ {error}</div>}

      <div className="jobs-list">
        {jobs.length === 0 && !loading && (
          <div className="empty-state">
            <p>No stored graphs found.</p>
            <p>Run a scan to create new provenance records!</p>
          </div>
        )}

        {jobs.map((job) => (
          <div
            key={job.job_id}
            className={`job-card ${selectedJob === job.job_id ? 'selected' : ''}`}
            onClick={() => loadGraph(job.job_id)}
          >
            <div className="job-header">
              <span className="job-id">📋 {job.job_id}</span>
              <span className={`status ${job.status}`}>{job.status}</span>
            </div>
            <div className="job-details">
              <div className="detail">
                <span className="label">Nodes:</span>
                <span className="value">{job.nodes_count}</span>
              </div>
              <div className="detail">
                <span className="label">Edges:</span>
                <span className="value">{job.edges_count}</span>
              </div>
              <div className="detail">
                <span className="label">Created:</span>
                <span className="value">{formatDate(job.created_at)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <style>{`
        .stored-graphs {
          padding: 1rem;
          background: #1a1a1a;
          border-radius: 8px;
          color: #fff;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }
        .header h2 {
          margin: 0;
          font-size: 1.5rem;
        }
        .refresh-btn {
          padding: 0.5rem 1rem;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }
        .refresh-btn:hover {
          background: #2563eb;
        }
        .loading, .error {
          padding: 1rem;
          text-align: center;
        }
        .error {
          color: #ef4444;
        }
        .jobs-list {
          display: grid;
          gap: 0.75rem;
        }
        .job-card {
          padding: 1rem;
          background: #2a2a2a;
          border: 2px solid #333;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .job-card:hover {
          border-color: #3b82f6;
          transform: translateY(-2px);
        }
        .job-card.selected {
          border-color: #10b981;
          background: #1e3a2f;
        }
        .job-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 0.5rem;
        }
        .job-id {
          font-family: monospace;
          font-size: 0.9rem;
        }
        .status {
          padding: 0.25rem 0.5rem;
          border-radius: 3px;
          font-size: 0.75rem;
          font-weight: bold;
          text-transform: uppercase;
        }
        .status.completed {
          background: #10b981;
          color: white;
        }
        .status.failed {
          background: #ef4444;
          color: white;
        }
        .status.running {
          background: #f59e0b;
          color: white;
        }
        .job-details {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 0.5rem;
          font-size: 0.85rem;
        }
        .detail {
          display: flex;
          flex-direction: column;
        }
        .label {
          color: #9ca3af;
          font-size: 0.75rem;
        }
        .value {
          font-weight: bold;
        }
        .empty-state {
          text-align: center;
          padding: 2rem;
          color: #9ca3af;
        }
      `}</style>
    </div>
  );
};

export default StoredGraphs;
