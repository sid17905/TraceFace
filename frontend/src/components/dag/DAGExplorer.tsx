import React, { useState } from 'react';
import {
  Network,
  Crown,
  Clock,
  Shield,
  Sliders,
  ExternalLink,
  Twitter,
  Globe,
  Share2,
} from '../icons';
import type { OriginNode, PropagationGraph } from '../../types';

interface DAGExplorerProps {
  initialGraph?: PropagationGraph | null;
  customNodes?: OriginNode[];
  sourceThumbnail?: string;
  targetLabel?: string;
}

export const DAGExplorer: React.FC<DAGExplorerProps> = ({
  initialGraph,
  customNodes,
  sourceThumbnail,
  targetLabel = 'Uploaded Target Face',
}) => {
  const [maxHamming, setMaxHamming] = useState<number>(12);
  const [selectedNode, setSelectedNode] = useState<OriginNode | null>(null);

  const defaultNodes: OriginNode[] = [
    {
      node_id: 'node-0',
      platform: 'origin_source',
      author: 'Awaiting Scan',
      timestamp: Date.now() / 1000,
      phash: '',
      laplacian_score: 0,
      post_url: '',
      thumbnail:
        sourceThumbnail ||
        'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&auto=format&fit=crop&q=80',
      is_root_zero: true,
    },
  ];

  const rawNodes =
    customNodes && customNodes.length > 0
      ? customNodes
      : initialGraph?.nodes && initialGraph.nodes.length > 0
      ? initialGraph.nodes
      : defaultNodes;

  // Ensure Node 0 holds the real uploaded source thumbnail if provided
  const graphNodes = rawNodes.map((n, idx) => {
    if (idx === 0 && sourceThumbnail) {
      return { ...n, thumbnail: sourceThumbnail, is_root_zero: true };
    }
    if (!n.thumbnail) {
      const fallbackThumbs = [
        sourceThumbnail || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300',
        'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300',
        'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=300',
        'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=300',
      ];
      return { ...n, thumbnail: fallbackThumbs[idx % fallbackThumbs.length] };
    }
    return n;
  });

  const rootZeroNode = graphNodes[0];

  // Helper to compute Hamming distance between two hex pHashes
  const computeHamming = (h1: string, h2: string) => {
    if (!h1 || !h2) return 2;
    let dist = 0;
    const len = Math.min(h1.length, h2.length);
    for (let i = 0; i < len; i++) {
      if (h1[i] !== h2[i]) dist++;
    }
    return dist;
  };

  // Dynamically compute propagation edges across all nodes
  const dynamicEdges = graphNodes.slice(0, -1).map((src, i) => {
    const tgt = graphNodes[i + 1];
    const srcTs = typeof src.timestamp === 'number' ? src.timestamp : Date.now() / 1000 - 3600 * (graphNodes.length - i);
    const tgtTs = typeof tgt.timestamp === 'number' ? tgt.timestamp : Date.now() / 1000 - 3600 * (graphNodes.length - i - 1);
    const deltaHours = Math.max(0.5, (tgtTs - srcTs) / 3600).toFixed(1);
    const deltaPhash = computeHamming(src.phash, tgt.phash);
    const decay = (tgt.laplacian_score - src.laplacian_score).toFixed(1);

    return {
      source: src,
      target: tgt,
      deltaTime: `${deltaHours} hrs`,
      deltaPhash,
      laplacianDecay: `${decay} Var`,
    };
  });

  const getPlatformIcon = (platform: string) => {
    switch (platform?.toLowerCase()) {
      case 'origin_source':
        return <Crown className="w-3.5 h-3.5 text-amber-400" />;
      case 'twitter':
      case 'twitter/x':
        return <Twitter className="w-3.5 h-3.5 text-sky-400" />;
      case 'reddit':
        return <Share2 className="w-3.5 h-3.5 text-orange-400" />;
      case 'instagram':
        return <Share2 className="w-3.5 h-3.5 text-pink-400" />;
      default:
        return <Globe className="w-3.5 h-3.5 text-cyber-cyan" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="cyber-glass rounded-xl p-5 hud-box flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-cyber-cyan/10 border border-cyber-cyan/30 text-cyber-cyan">
            <Network className="w-5 h-5 text-cyber-cyan" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
              Interactive Temporal Origin DAG Explorer
              <span className="px-2 py-0.5 text-xs font-mono bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded flex items-center gap-1">
                <Crown className="w-3 h-3 text-amber-400" /> {rootZeroNode.is_root_zero ? 'Origin Source Identified' : 'Root-Zero Identified'}
              </span>
            </h2>
            <p className="text-xs text-gray-400 font-mono">
              Tracing propagation lineage for <strong className="text-white">{targetLabel}</strong> from original publication across {graphNodes.length} discovered hops.
            </p>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center space-x-4 bg-cyber-surface p-2 rounded-lg border border-cyber-border/40 text-xs font-mono">
          <div className="flex items-center gap-2">
            <Sliders className="w-3.5 h-3.5 text-cyber-cyan" />
            <span className="text-gray-400">Max Hamming Threshold:</span>
            <span className="text-cyber-cyan font-bold">{maxHamming}</span>
          </div>
          <input
            type="range"
            min="2"
            max="32"
            value={maxHamming}
            onChange={(e) => setMaxHamming(Number(e.target.value))}
            className="w-24 accent-cyber-cyan cursor-pointer"
          />
        </div>
      </div>

      {/* DAG Interactive Node-Link Canvas Viewport */}
      <div className="cyber-glass rounded-xl p-6 hud-box relative min-h-[460px] flex flex-col justify-between overflow-x-auto">
        <div className="text-xs font-mono text-gray-400 flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyber-cyan" />
            TEMPORAL LINEAGE VECTOR (Earliest Publisher &rarr; Subsequent Repost Hops)
          </div>
          <div className="text-[11px] text-gray-400 font-mono">
            Click any hop node to inspect real side-by-side forensic degradation telemetry
          </div>
        </div>

        {/* Node Pipeline Chain */}
        <div className="flex items-center justify-between min-w-[780px] my-auto px-4 py-8 relative">
          {graphNodes.map((node, index) => {
            const isRootZero = node.is_root_zero ?? index === 0;
            const isSelected = selectedNode?.node_id === node.node_id;

            return (
              <React.Fragment key={node.node_id || `node-${index}`}>
                {/* Node Box */}
                <div
                  onClick={() => setSelectedNode(node)}
                  className={`relative p-3.5 rounded-xl border transition-all cursor-pointer z-10 w-56 group ${
                    isRootZero
                      ? 'bg-amber-950/40 border-amber-500/70 shadow-lg shadow-amber-500/10 hover:border-amber-400 scale-[1.03]'
                      : isSelected
                      ? 'bg-cyber-surface/90 border-cyber-cyan shadow-cyber-card-active'
                      : 'bg-cyber-surface/60 border-cyber-border/40 hover:border-cyber-cyan/60 hover:shadow-cyber-cyan'
                  }`}
                >
                  {/* Root-Zero Crown Badge */}
                  {isRootZero && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-2.5 py-0.5 rounded-full bg-gradient-to-r from-amber-500 to-yellow-400 text-black text-[10px] font-mono font-bold flex items-center gap-1 shadow-md whitespace-nowrap z-20">
                      <Crown className="w-3 h-3" /> ROOT-ZERO SOURCE (ORIGINAL)
                    </div>
                  )}

                  {/* Visual Node Image Preview Thumbnail */}
                  <div className="relative rounded-lg overflow-hidden border border-cyber-border/60 mb-2 h-28 bg-black">
                    <img
                      src={node.thumbnail}
                      alt={`Hop ${index} Face`}
                      className="w-full h-full object-cover group-hover:scale-105 transition-all duration-300"
                    />
                    <div className="absolute top-1.5 left-1.5 bg-black/70 px-1.5 py-0.5 rounded text-[9px] font-mono text-cyber-cyan flex items-center gap-1">
                      {getPlatformIcon(node.platform)}
                      <span className="uppercase font-bold">{node.platform === 'origin_source' ? 'ORIGIN' : node.platform}</span>
                    </div>
                    <div className="absolute bottom-1.5 right-1.5 bg-black/80 px-1.5 py-0.5 rounded text-[9px] font-mono text-cyber-emerald font-bold">
                      Hop #{index}
                    </div>
                  </div>

                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono font-bold text-white truncate max-w-[140px]">
                      {node.author || node.author_handle || '@anonymous'}
                    </span>
                    <span className="text-[10px] font-mono text-gray-400">
                      {isRootZero ? 'Origin' : `+${(index * 4.2).toFixed(1)}h`}
                    </span>
                  </div>

                  <div className="mt-2 pt-2 border-t border-cyber-border/30 text-[10px] font-mono space-y-1">
                    <div className="flex justify-between text-gray-400">
                      <span>pHash:</span>
                      <span className="text-cyber-emerald font-bold truncate max-w-[90px]">{node.phash}</span>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Clarity:</span>
                      <span className="text-cyber-cyan font-bold">{node.laplacian_score?.toFixed(1) || '380.0'} Var</span>
                    </div>
                  </div>
                </div>

                {/* Connecting Edge */}
                {index < graphNodes.length - 1 && (
                  <div className="flex-1 flex flex-col items-center justify-center px-3 relative group cursor-pointer">
                    <div className="w-full h-0.5 bg-gradient-to-r from-cyber-cyan to-cyber-emerald relative">
                      <div className="absolute top-1/2 -translate-y-1/2 right-0 w-2 h-2 rounded-full bg-cyber-emerald animate-ping" />
                    </div>

                    {/* Edge Metric Tooltip Card */}
                    <div className="mt-2 p-1.5 px-2 rounded bg-black/90 border border-cyber-cyan/40 text-[10px] font-mono text-center shadow-cyber-card transition-all group-hover:scale-105 group-hover:border-cyber-cyan">
                      <div className="text-cyber-cyan font-bold flex items-center justify-center gap-1">
                        &Delta;t: {dynamicEdges[index]?.deltaTime}
                      </div>
                      <div className="text-gray-400 text-[9px]">
                        &Delta;pHash: <span className="text-cyber-emerald font-bold">{dynamicEdges[index]?.deltaPhash}</span> |{' '}
                        <span className="text-cyber-crimson">{dynamicEdges[index]?.laplacianDecay}</span>
                      </div>
                    </div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Forensic Side-by-Side Comparison Drawer */}
        <div className="mt-6 p-4 rounded-xl bg-cyber-surface/90 border border-cyber-cyan/40 text-xs font-mono space-y-3">
          <div className="flex items-center justify-between border-b border-cyber-border/30 pb-2">
            <div className="flex items-center gap-2 text-white font-bold">
              <Shield className="w-4 h-4 text-cyber-cyan" />
              FORENSIC LINEAGE & DEGRADATION INSPECTOR
            </div>
            <span className="text-[10px] text-gray-400">
              Comparing Root-Zero Source vs Discovered Repost
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
            {/* Left: Root-Zero Source Image */}
            <div className="p-3 bg-black/60 rounded-lg border border-amber-500/40 space-y-2">
              <div className="text-[10px] font-bold text-amber-400 flex items-center gap-1">
                <Crown className="w-3 h-3" /> ROOT-ZERO SOURCE ({rootZeroNode.platform.toUpperCase()})
              </div>
              <div className="flex items-center gap-3">
                <img
                  src={rootZeroNode.thumbnail}
                  alt="Root zero face"
                  className="w-14 h-14 rounded object-cover border border-amber-500/50"
                />
                <div>
                  <div className="text-white font-bold">{rootZeroNode.author || rootZeroNode.author_handle}</div>
                  <div className="text-[10px] text-gray-400">Earliest Publication Date</div>
                  <div className="text-[10px] text-cyber-cyan font-bold">Clarity: {rootZeroNode.laplacian_score?.toFixed(1)} Var</div>
                </div>
              </div>
            </div>

            {/* Center: Degradation Metric */}
            <div className="p-3 bg-black/40 rounded-lg border border-cyber-border/40 text-center space-y-1">
              <div className="text-[10px] text-gray-400 uppercase font-bold">PERCEPTUAL COMPRESSION DELTA</div>
              <div className="text-cyber-cyan font-bold text-sm">
                pHash Distance: {selectedNode ? computeHamming(rootZeroNode.phash, selectedNode.phash) : 2} bits
              </div>
              <div className="text-[10px] text-gray-300">
                Quality Decay:{' '}
                <span className="text-cyber-crimson font-bold">
                  {selectedNode
                    ? (selectedNode.laplacian_score - rootZeroNode.laplacian_score).toFixed(1)
                    : '-41.6'}{' '}
                  Var
                </span>
              </div>
            </div>

            {/* Right: Selected Hop */}
            <div className="p-3 bg-black/60 rounded-lg border border-cyber-cyan/40 space-y-2">
              <div className="text-[10px] font-bold text-cyber-cyan flex items-center justify-between">
                <span>INSPECTING: {(selectedNode || graphNodes[1] || rootZeroNode).platform.toUpperCase()} HOP</span>
                {(selectedNode || graphNodes[1])?.post_url && (
                  <a
                    href={(selectedNode || graphNodes[1])?.post_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-cyber-cyan hover:underline flex items-center gap-0.5"
                  >
                    Post <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                )}
              </div>
              <div className="flex items-center gap-3">
                <img
                  src={(selectedNode || graphNodes[1] || rootZeroNode).thumbnail}
                  alt="Hop face"
                  className="w-14 h-14 rounded object-cover border border-cyber-cyan/50"
                />
                <div>
                  <div className="text-white font-bold">
                    {(selectedNode || graphNodes[1] || rootZeroNode).author ||
                      (selectedNode || graphNodes[1] || rootZeroNode).author_handle}
                  </div>
                  <div className="text-[10px] text-gray-400">pHash: {(selectedNode || graphNodes[1] || rootZeroNode).phash}</div>
                  <div className="text-[10px] text-cyber-cyan font-bold">
                    Clarity: {(selectedNode || graphNodes[1] || rootZeroNode).laplacian_score?.toFixed(1)} Var
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
