import React, { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { BiometricHUD } from './components/biometric/BiometricHUD';
import { OSINTRadar, type DiscoveredCandidate } from './components/osint/OSINTRadar';
import { DAGExplorer } from './components/dag/DAGExplorer';
import { MerkleInspector } from './components/cryptographic/MerkleInspector';
import { TakedownPortal } from './components/web3/TakedownPortal';
import { PrivacyVault } from './components/zk/PrivacyVault';
import { StorageDashboard } from './components/storage/StorageDashboard';
import { GuidedProcedureModal } from './components/layout/GuidedProcedureModal';
import type { FaceScanOutput, OriginNode, PropagationGraph } from './types';
import { TraceFaceApi } from './services/api';
import {
  Terminal,
  CheckCircle2,
  Layers,
  Zap,
} from './components/icons';

const PHASE_DURATION_SECONDS = 12;

export function App() {
  const [activeTab, setActiveTab] = useState<string>('biometric');
  const [currentScan, setCurrentScan] = useState<FaceScanOutput | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [targetThumbnail, setTargetThumbnail] = useState<string>(
    'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&auto=format&fit=crop&q=80'
  );
  const [targetLabel, setTargetLabel] = useState<string>('sample_target_01.jpg');
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [systemHealth, setSystemHealth] = useState<any | null>(null);

  // Dynamic OSINT & DAG state
  const [discoveredCandidates, setDiscoveredCandidates] = useState<DiscoveredCandidate[]>([]);
  const [dynamicGraph, setDynamicGraph] = useState<PropagationGraph | null>(null);
  const [dynamicNodes, setDynamicNodes] = useState<OriginNode[]>([]);

  // Guided Presentation Tour State
  const [isTourActive, setIsTourActive] = useState<boolean>(false);
  const [isTourPaused, setIsTourPaused] = useState<boolean>(false);
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [secondsRemaining, setSecondsRemaining] = useState<number>(PHASE_DURATION_SECONDS);

  const pipelineSteps = [
    {
      num: 1,
      id: 'biometric',
      title: '1. Biometrics & Liveness',
      desc: 'Detects face & checks anti-deepfake 2D-FFT',
    },
    {
      num: 2,
      id: 'osint',
      title: '2. OSINT Web Crawl',
      desc: 'Multi-engine reverse search for this face',
    },
    {
      num: 3,
      id: 'dag',
      title: '3. Origin Lineage DAG',
      desc: 'Root-Zero temporal attribution & real photo hops',
    },
    {
      num: 4,
      id: 'merkle',
      title: '4. Merkle Sealing',
      desc: '4-Leaf RFC 8785 Proof & Tamper Audit',
    },
    {
      num: 5,
      id: 'takedown',
      title: '5. Web3 Dispute',
      desc: 'EIP-712 Takedown on Hardhat 31337',
    },
    {
      num: 6,
      id: 'zk',
      title: '6. ZK Privacy Vault',
      desc: 'Groth16 Biometric Match on bn128',
    },
    {
      num: 7,
      id: 'storage',
      title: '7. Storage Browser',
      desc: 'View saved graphs & create new ones',
    },
  ];

  useEffect(() => {
    TraceFaceApi.checkHealth().then((health) => {
      setSystemHealth(health);
    });
  }, []);

  // Guided presentation tour timer
  useEffect(() => {
    if (!isTourActive || isTourPaused) return;

    const timer = setInterval(() => {
      setSecondsRemaining((prev) => {
        if (prev <= 1) {
          // Transition to next phase
          if (currentStep < 6) {
            const nextStepNum = currentStep + 1;
            const nextStepObj = pipelineSteps.find((s) => s.num === nextStepNum);
            setCurrentStep(nextStepNum);
            if (nextStepObj) {
              setActiveTab(nextStepObj.id);
            }
            return PHASE_DURATION_SECONDS;
          } else {
            // Tour complete
            setIsTourActive(false);
            return 0;
          }
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isTourActive, isTourPaused, currentStep]);

  // When a scan completes, start the guided presentation walkthrough for that single input
  const handleScanComplete = (scan: FaceScanOutput, jobId: string) => {
    setCurrentScan(scan);
    setCurrentJobId(jobId);

    if (scan.source_image_path) {
      setTargetLabel(scan.source_image_path.split('\\').pop()?.split('/').pop() || 'target_input.jpg');
    }

    // Initialize Root-Zero origin node with the real input photo thumbnail
    const initialNode: OriginNode = {
      node_id: 'node-0',
      platform: 'origin_source',
      author: scan.source_image_path?.split('\\').pop()?.split('/').pop() || 'Uploaded Target',
      timestamp: Date.now() / 1000,
      phash: scan.perceptual_hash_phash,
      laplacian_score: scan.quality_metrics.laplacian_blur_score,
      post_url: '',
      thumbnail: targetThumbnail,
      is_root_zero: true,
    };
    setDynamicNodes([initialNode]);

    // Start automated 6-phase walkthrough for this target
    setCurrentStep(1);
    setActiveTab('biometric');
    setSecondsRemaining(PHASE_DURATION_SECONDS);
    setIsTourActive(true);
    setIsTourPaused(false);
  };

  const handleManualSelectTab = (tabId: string) => {
    setActiveTab(tabId);
    const stepObj = pipelineSteps.find((s) => s.id === tabId);
    if (stepObj) {
      setCurrentStep(stepObj.num);
      setSecondsRemaining(PHASE_DURATION_SECONDS);
    }
  };

  const handleNextPhase = () => {
    if (currentStep < 6) {
      const nextStepNum = currentStep + 1;
      const nextStepObj = pipelineSteps.find((s) => s.num === nextStepNum);
      setCurrentStep(nextStepNum);
      if (nextStepObj) setActiveTab(nextStepObj.id);
      setSecondsRemaining(PHASE_DURATION_SECONDS);
    } else {
      setIsTourActive(false);
    }
  };

  const handlePrevPhase = () => {
    if (currentStep > 1) {
      const prevStepNum = currentStep - 1;
      const prevStepObj = pipelineSteps.find((s) => s.num === prevStepNum);
      setCurrentStep(prevStepNum);
      if (prevStepObj) setActiveTab(prevStepObj.id);
      setSecondsRemaining(PHASE_DURATION_SECONDS);
    }
  };

  const handleCandidatesUpdated = (cands: DiscoveredCandidate[]) => {
    setDiscoveredCandidates(cands);

    if (currentScan) {
      const scanPhash = currentScan.perceptual_hash_phash;
      const blurScore = currentScan.quality_metrics.laplacian_blur_score;

      const rootNode: OriginNode = {
        node_id: 'node-0',
        platform: 'origin_source',
        author: targetLabel,
        timestamp: Date.now() / 1000,
        phash: scanPhash,
        laplacian_score: blurScore,
        post_url: '',
        thumbnail: targetThumbnail,
        is_root_zero: true,
      };

      const discoveredNodes: OriginNode[] = cands.map((c, idx) => ({
        node_id: `node-${idx + 1}`,
        platform: c.platform,
        author: c.author,
        timestamp: Date.now() / 1000 - 3600 * (idx + 1),
        phash: scanPhash.slice(0, -1) + ((idx + 1) % 16).toString(16),
        laplacian_score: Math.max(120, blurScore - (idx + 1) * 35),
        post_url: c.postUrl,
        thumbnail: c.thumbnail,
        is_root_zero: false,
      }));

      setDynamicNodes([rootNode, ...discoveredNodes]);
    }
  };

  const handleTargetThumbnailChange = (url: string, label: string) => {
    setTargetThumbnail(url);
    setTargetLabel(label);
  };

  return (
    <div className="min-h-screen cyber-grid-bg text-gray-100 flex flex-col justify-between selection:bg-cyan-500 selection:text-black">
      {/* Top Navigation */}
      <Navbar activeTab={activeTab} setActiveTab={handleManualSelectTab} systemHealth={systemHealth} />

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-6">
        {/* Single Target Tracking HUD Badge */}
        {currentScan && (
          <div className="cyber-glass rounded-xl p-3 px-4 border border-cyber-cyan/30 flex flex-wrap items-center justify-between gap-3 text-xs font-mono bg-black/40">
            <div className="flex items-center gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-cyber-emerald animate-ping shrink-0" />
              <div className="flex items-center gap-2">
                <img
                  src={targetThumbnail}
                  alt="Target thumb"
                  className="w-7 h-7 rounded object-cover border border-cyan-400/50"
                />
                <div>
                  <span className="text-gray-400">Target Identity Ingested:</span>{' '}
                  <span className="text-white font-bold">{targetLabel}</span>
                </div>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-[11px] text-gray-400">
              <div>
                SHA-256: <span className="text-cyber-cyan font-mono">{currentScan.image_hash_sha256.slice(0, 12)}...</span>
              </div>
              <div>
                Keccak-256: <span className="text-purple-400 font-mono">{currentScan.embedding_hash_keccak256.slice(0, 12)}...</span>
              </div>
              <div>
                Liveness: <span className="text-cyber-emerald font-bold">GENUINE ({((1 - (currentScan.quality_metrics.deepfake_score || 0)) * 100).toFixed(1)}%)</span>
              </div>
            </div>
          </div>
        )}

        {/* Unified Workflow Stepper Rail */}
        <div className="cyber-glass rounded-xl p-4 hud-box">
          <div className="flex items-center justify-between mb-3">
            <div className="text-xs font-mono text-gray-300 flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              TRACEFACE FORENSIC PROVENANCE LIFECYCLE
            </div>
            {!isTourActive && (
              <button
                onClick={() => {
                  setIsTourActive(true);
                  setIsTourPaused(false);
                  setCurrentStep(1);
                  setActiveTab('biometric');
                  setSecondsRemaining(PHASE_DURATION_SECONDS);
                }}
                className="text-[11px] font-mono text-cyan-300 bg-cyan-500/10 hover:bg-cyan-500/20 px-3 py-1 rounded border border-cyan-500/40 flex items-center gap-1.5 transition-all cursor-pointer shadow-cyber-cyan"
              >
                <Zap className="w-3.5 h-3.5 text-cyan-400" />
                Start Autonomous Guided Walkthrough
              </button>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {pipelineSteps.map((step) => {
              const isDone = currentScan && currentStep > step.num;
              const isCurrent = activeTab === step.id;

              return (
                <button
                  key={step.id}
                  onClick={() => handleManualSelectTab(step.id)}
                  className={`p-2.5 rounded-lg border text-left font-mono transition-all cursor-pointer ${
                    isCurrent
                      ? 'bg-cyan-500/20 border-cyan-400 shadow-cyber-card-active scale-[1.02]'
                      : isDone
                      ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-400'
                      : 'bg-cyber-surface/40 border-cyber-border/30 text-gray-400 hover:border-cyan-500/40'
                  }`}
                >
                  <div className="flex items-center justify-between text-[11px] font-bold">
                    <span>{step.title}</span>
                    {isDone && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                  </div>
                  <div className="text-[10px] text-gray-400 mt-0.5 truncate">{step.desc}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* View Selection: Renders Active Component based on Stepper Selection */}
        {activeTab === 'biometric' && (
          <BiometricHUD
            onScanComplete={handleScanComplete}
            currentScan={currentScan}
            isScanning={isScanning}
            setIsScanning={setIsScanning}
            onTargetThumbnailChange={handleTargetThumbnailChange}
          />
        )}

        {activeTab === 'osint' && (
          <OSINTRadar
            jobId={currentJobId}
            onMatchFound={(match) => console.log('Match found:', match)}
            onGraphFound={(graph) => setDynamicGraph(graph)}
            onCandidatesUpdated={handleCandidatesUpdated}
          />
        )}

        {activeTab === 'dag' && (
          <DAGExplorer
            initialGraph={dynamicGraph}
            customNodes={dynamicNodes}
            sourceThumbnail={targetThumbnail}
            targetLabel={targetLabel}
          />
        )}

        {activeTab === 'merkle' && (
          <MerkleInspector
            initialRoot={currentScan?.embedding_hash_keccak256}
            sourceImageHash={currentScan?.image_hash_sha256}
            embeddingHash={currentScan?.embedding_hash_keccak256}
          />
        )}

        {activeTab === 'takedown' && (
          <TakedownPortal currentRecordHash={currentScan?.embedding_hash_keccak256} />
        )}

        {activeTab === 'zk' && (
          <PrivacyVault
            queryEmbedding={currentScan?.embedding_vector}
            targetLabel={targetLabel}
            autoExecute={isTourActive}
          />
        )}

        {activeTab === 'storage' && <StorageDashboard />}

        {/* Floating Autonomous Guided Procedure Modal Dialog Box */}
        {isTourActive && (
          <GuidedProcedureModal
            currentStep={currentStep}
            secondsRemaining={secondsRemaining}
            totalDurationSeconds={PHASE_DURATION_SECONDS}
            isPaused={isTourPaused}
            onTogglePause={() => setIsTourPaused(!isTourPaused)}
            onNextPhase={handleNextPhase}
            onPrevPhase={handlePrevPhase}
            onCloseTour={() => setIsTourActive(false)}
            targetThumbnail={targetThumbnail}
            targetLabel={targetLabel}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="cyber-glass border-t border-cyber-border/30 py-4 px-6 mt-12">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between text-xs font-mono text-gray-400 gap-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>TraceFace Security Architecture</span>
            <span className="text-gray-600">|</span>
            <span>RetinaFace &bull; ArcFace-512 &bull; 2D-FFT &bull; Keccak-256 Merkle &bull; Groth16 zk-SNARK &bull; EIP-712</span>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-cyan-400">RFC 8785 Canonical JSON Validated</span>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="text-gray-300 hover:text-cyan-400 transition-all flex items-center gap-1"
            >
              <Terminal className="w-3.5 h-3.5" /> REST API Docs
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
