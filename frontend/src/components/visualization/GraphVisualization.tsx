/**
 * Interactive Graph Visualization Dashboard
 * 
 * Uses D3.js force layout to render temporal origin DAGs.
 * Supports zooming, panning, node selection, and platform filtering.
 */

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { PropagationGraph, OriginNode } from '../../types';

interface GraphVisualizationProps {
  graph: PropagationGraph;
  width?: number;
  height?: number;
  onNodeSelect?: (node: OriginNode) => void;
}

interface D3Node extends d3.SimulationNodeDatum {
  id: string;
  platform: string;
  author?: string;
  url?: string;
  similarity?: number;
  is_root?: boolean;
}

interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  hamming?: number;
  delta?: number;
}

const PLATFORM_COLORS: Record<string, string> = {
  twitter: '#1DA1F2',
  reddit: '#FF4500',
  instagram: '#E4405F',
  linkedin: '#0A66C2',
  youtube: '#FF0000',
  tiktok: '#000000',
  facebook: '#1877F2',
};

export const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  graph,
  width = 800,
  height = 600,
  onNodeSelect,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [zoom, setZoom] = useState(1);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);

  useEffect(() => {
    if (!svgRef.current || !graph.nodes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Create zoom behavior
    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoomBehavior);

    // Create container group
    const g = svg.append('g');

    // Convert nodes
    const nodes: D3Node[] = graph.nodes.map((n) => ({
      id: n.node_id,
      platform: n.platform,
      author: n.author_handle || n.author || '',
      url: n.post_url,
      similarity: n.similarity_score || 0,
      is_root: n.is_root_zero,
      x: width / 2,
      y: height / 2,
    }));

    // Convert links
    const links: D3Link[] = graph.edges.map((e) => ({
      source: nodes.find((n) => n.id === e.source_id)!,
      target: nodes.find((n) => n.id === e.target_id)!,
      hamming: e.hamming_distance || 0,
      delta: e.time_delta_seconds || 0,
    }));

    // Create force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink<D3Node, D3Link>(links).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    // Draw links
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 2);

    // Draw nodes
    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g')
      .attr('cursor', 'pointer')
      .call(d3.drag<SVGGElement, D3Node>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    // Add circles
    node.append('circle')
      .attr('r', (d) => d.is_root ? 25 : 20)
      .attr('fill', (d) => PLATFORM_COLORS[d.platform] || '#808080')
      .attr('stroke', (d) => d.is_root ? '#FFD700' : '#fff')
      .attr('stroke-width', (d) => d.is_root ? 3 : 2);

    // Add labels
    node.append('text')
      .text((d) => d.platform)
      .attr('text-anchor', 'middle')
      .attr('dy', 4)
      .attr('fill', '#fff')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold');

    // Add hover effect
    node.append('title')
      .text((d) => `${d.platform}\n${d.author}\nSimilarity: ${(d.similarity || 0).toFixed(3)}`);

    // Click handler
    node.on('click', (event, d) => {
      event.stopPropagation();
      const originalNode = graph.nodes.find(n => n.node_id === d.id);
      if (originalNode && onNodeSelect) {
        onNodeSelect(originalNode);
      }
    });

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as D3Node).x!)
        .attr('y1', (d) => (d.source as D3Node).y!)
        .attr('x2', (d) => (d.target as D3Node).x!)
        .attr('y2', (d) => (d.target as D3Node).y!);

      node.attr('transform', (d) => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [graph, width, height]);

  // Platform filter buttons
  const platforms = [...new Set(graph.nodes.map(n => n.platform))];

  return (
    <div className="graph-visualization">
      <div className="controls">
        <div className="platform-filters">
          <button
            className={`filter-btn ${selectedPlatform === null ? 'active' : ''}`}
            onClick={() => setSelectedPlatform(null)}
          >
            All Platforms
          </button>
          {platforms.map((platform) => (
            <button
              key={platform}
              className={`filter-btn ${selectedPlatform === platform ? 'active' : ''}`}
              onClick={() => setSelectedPlatform(platform)}
              style={{ borderColor: PLATFORM_COLORS[platform] }}
            >
              {platform}
            </button>
          ))}
        </div>
      </div>

      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{ border: '1px solid #ccc' }}
      />

      <style>{`
        .graph-visualization {
          position: relative;
        }
        .controls {
          margin-bottom: 1rem;
        }
        .platform-filters {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }
        .filter-btn {
          padding: 0.5rem 1rem;
          border: 2px solid #ccc;
          border-radius: 0.5rem;
          background: white;
          cursor: pointer;
          transition: all 0.2s;
        }
        .filter-btn.active {
          background: #f0f0f0;
          font-weight: bold;
        }
        .filter-btn:hover {
          background: #f5f5f5;
        }
      `}</style>
    </div>
  );
};

export default GraphVisualization;
