/**
 * Storage Dashboard
 * 
 * Browse stored graphs and create new ones.
 */

import React, { useState } from 'react';
import StoredGraphs from './StoredGraphs';
import AddNewGraph from './AddNewGraph';
import GraphVisualization from '../visualization/GraphVisualization';
import type { PropagationGraph } from '../../types';

export const StorageDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'browse' | 'add'>('browse');
  const [selectedGraph, setSelectedGraph] = useState<{
    graph: PropagationGraph;
    jobId: string;
  } | null>(null);

  const handleGraphSelect = (graph: PropagationGraph, jobId: string) => {
    setSelectedGraph({ graph, jobId });
  };

  const handleGraphCreated = (graph: PropagationGraph, jobId: string) => {
    setSelectedGraph({ graph, jobId });
    setActiveTab('browse'); // Switch to browse tab after creation
  };

  return (
    <div className="storage-dashboard">
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'browse' ? 'active' : ''}`}
          onClick={() => setActiveTab('browse')}
        >
          📂 Browse Stored Graphs
        </button>
        <button
          className={`tab ${activeTab === 'add' ? 'active' : ''}`}
          onClick={() => setActiveTab('add')}
        >
          ➕ Add New Graph
        </button>
      </div>

      <div className="content">
        <div className="left-panel">
          {activeTab === 'browse' ? (
            <StoredGraphs onGraphSelect={handleGraphSelect} />
          ) : (
            <AddNewGraph onGraphCreated={handleGraphCreated} />
          )}
        </div>

        <div className="right-panel">
          {selectedGraph ? (
            <div className="graph-display">
              <div className="graph-header">
                <h3>📊 Graph: {selectedGraph.jobId}</h3>
                <p>
                  {selectedGraph.graph.nodes.length} nodes • {selectedGraph.graph.edges.length} edges
                </p>
              </div>
              <GraphVisualization
                graph={selectedGraph.graph}
                width={600}
                height={500}
              />
              <div className="graph-details">
                <h4>Root Zero (Original Source)</h4>
                {selectedGraph.graph.nodes
                  .filter((n) => n.is_root_zero)
                  .map((node) => (
                    <div key={node.node_id} className="node-card root">
                      <div className="platform">{node.platform}</div>
                      <div className="author">{node.author_handle}</div>
                      <a href={node.post_url} target="_blank" rel="noopener noreferrer">
                        🔗 View Post
                      </a>
                    </div>
                  ))}
                
                <h4>Propagation Path</h4>
                {selectedGraph.graph.edges.map((edge, i) => {
                  const sourceNode = selectedGraph.graph.nodes.find(
                    (n) => n.node_id === edge.source_id
                  );
                  const targetNode = selectedGraph.graph.nodes.find(
                    (n) => n.node_id === edge.target_id
                  );
                  return (
                    <div key={i} className="edge-card">
                      <span className="source">{sourceNode?.platform}</span>
                      <span className="arrow">→</span>
                      <span className="target">{targetNode?.platform}</span>
                      <span className="delta">({(edge.time_delta_seconds || 0).toFixed(0)}s)</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <p>👈 Select a graph to visualize</p>
            </div>
          )}
        </div>
      </div>

      <style>{`
        .storage-dashboard {
          height: 100vh;
          display: flex;
          flex-direction: column;
          background: #0a0a0a;
          color: #fff;
          padding: 1rem;
        }
        .tabs {
          display: flex;
          gap: 0.5rem;
          margin-bottom: 1rem;
        }
        .tab {
          flex: 1;
          padding: 1rem;
          background: #1a1a1a;
          border: 2px solid #333;
          border-radius: 6px;
          color: #9ca3af;
          font-size: 1rem;
          font-weight: bold;
          cursor: pointer;
          transition: all 0.2s;
        }
        .tab:hover {
          background: #2a2a2a;
        }
        .tab.active {
          background: #1e3a8a;
          border-color: #3b82f6;
          color: white;
        }
        .content {
          flex: 1;
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
          overflow: hidden;
        }
        .left-panel, .right-panel {
          overflow-y: auto;
        }
        .right-panel {
          background: #1a1a1a;
          border-radius: 8px;
          padding: 1rem;
        }
        .graph-display {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        .graph-header {
          border-bottom: 1px solid #333;
          padding-bottom: 1rem;
        }
        .graph-header h3 {
          margin: 0 0 0.5rem 0;
        }
        .graph-header p {
          margin: 0;
          color: #9ca3af;
        }
        .graph-details {
          margin-top: 1rem;
        }
        .graph-details h4 {
          margin: 1rem 0 0.5rem 0;
          color: #9ca3af;
        }
        .node-card {
          padding: 1rem;
          background: #2a2a2a;
          border-radius: 6px;
          margin-bottom: 0.5rem;
        }
        .node-card.root {
          background: #064e3b;
          border-left: 3px solid #10b981;
        }
        .platform {
          font-weight: bold;
          margin-bottom: 0.25rem;
        }
        .author {
          color: #9ca3af;
          font-size: 0.9rem;
          margin-bottom: 0.5rem;
        }
        .edge-card {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem;
          background: #2a2a2a;
          border-radius: 4px;
          margin-bottom: 0.25rem;
          font-size: 0.9rem;
        }
        .arrow {
          color: #3b82f6;
        }
        .delta {
          color: #9ca3af;
          margin-left: auto;
        }
        .empty-state {
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #6b7280;
          font-size: 1.25rem;
        }
      `}</style>
    </div>
  );
};

export default StorageDashboard;
