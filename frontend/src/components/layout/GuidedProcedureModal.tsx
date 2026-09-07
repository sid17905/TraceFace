import React, { useState } from 'react';
import {
  Activity,
  CheckCircle2,
  Zap,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from '../icons';

export interface PhaseInfo {
  num: number;
  id: string;
  title: string;
  subtitle: string;
  mission: string;
  substeps: Array<{ text: string; delaySeconds: number }>;
  realDataLabel?: string;
  realDataValue?: string;
}

interface GuidedProcedureModalProps {
  currentStep: number;
  secondsRemaining: number;
  totalDurationSeconds: number;
  isPaused: boolean;
  onTogglePause: () => void;
  onNextPhase: () => void;
  onPrevPhase: () => void;
  onCloseTour: () => void;
  targetThumbnail?: string;
  targetLabel?: string;
}

export const GuidedProcedureModal: React.FC<GuidedProcedureModalProps> = ({
  currentStep,
  secondsRemaining,
  totalDurationSeconds,
  isPaused,
  onTogglePause,
  onNextPhase,
  onPrevPhase,
  onCloseTour,
  targetThumbnail,
  targetLabel = 'Target Face',
}) => {
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const elapsed = totalDurationSeconds - secondsRemaining;

  const phaseData: Record<number, PhaseInfo> = {
    1: {
      num: 1,
      id: 'biometric',
      title: 'Biometrics & 2D-FFT Liveness Forensics',
      subtitle: 'RetinaFace Landmark Extraction & Anti-Deepfake Gate',
      mission:
        'Scanning your photo to locate 5 facial landmarks, testing 2D-FFT frequency spectrum to reject AI deepfakes, and generating a 512-dimensional ArcFace vector.',
      substeps: [
        { text: 'RetinaFace 5-point landmark detection & bounding box normalization', delaySeconds: 1 },
        { text: '2D-FFT azimuthal power spectrum deepfake analysis (Genuine Human)', delaySeconds: 4 },
        { text: '512-D ArcFace continuous embedding extracted & Keccak-256 sealed', delaySeconds: 8 },
      ],
      realDataLabel: 'Biometric Status',
      realDataValue: 'LIVENESS VERIFIED (100% Genuine)',
    },
    2: {
      num: 2,
      id: 'osint',
      title: 'Multi-Engine OSINT Reverse Search',
      subtitle: 'Google Lens & Playwright Cluster Crawl',
      mission:
        'Crawling social media and web archives to locate everywhere this exact face appears online, filtering candidate hits with cosine similarity (threshold >= 0.68).',
      substeps: [
        { text: 'Multi-engine reverse search query dispatched across social networks', delaySeconds: 1 },
        { text: 'In-memory candidate media ingestion & perceptual hash comparison', delaySeconds: 4 },
        { text: 'Biometric similarity gate enforced (3 matching targets captured)', delaySeconds: 8 },
      ],
      realDataLabel: 'OSINT Match Gate',
      realDataValue: '3 Target(s) Captured across Web',
    },
    3: {
      num: 3,
      id: 'dag',
      title: 'Temporal Origin Lineage DAG',
      subtitle: 'Root-Zero Source Attribution & Degradation Vector',
      mission:
        'Sorting discovered posts by earliest publication timestamp and image clarity to identify Root-Zero (original creator) and measure compression decay.',
      substeps: [
        { text: 'Temporal chronological sorting by UTC publication timestamps', delaySeconds: 1 },
        { text: 'Root-Zero source identified: Earliest post with maximum sharpness', delaySeconds: 4 },
        { text: 'Perceptual pHash Hamming degradation mapped across lineage hops', delaySeconds: 8 },
      ],
      realDataLabel: 'Root-Zero Source',
      realDataValue: 'Twitter/X (@source_origin_zero)',
    },
    4: {
      num: 4,
      id: 'merkle',
      title: '4-Leaf RFC 8785 Merkle Tree Sealing',
      subtitle: 'Deterministic Cryptographic Provenance Sealing',
      mission:
        'Packaging source image, ArcFace embedding, social metadata, and target match into a 4-leaf Merkle Tree root. Any 1-byte alteration collapses the root immediately.',
      substeps: [
        { text: 'Canonical RFC 8785 JSON structured serialization compiled', delaySeconds: 1 },
        { text: '4-Leaf Keccak-256 Merkle Tree root generated and verified', delaySeconds: 4 },
        { text: 'Decentralized IPFS immutable content address (CID) pinned', delaySeconds: 8 },
      ],
      realDataLabel: 'Provenance Root',
      realDataValue: '0x6f8bb6c1eb7a2e10... (EVM Verified)',
    },
    5: {
      num: 5,
      id: 'takedown',
      title: 'Web3 Identity Takedown & Dispute',
      subtitle: 'EIP-712 Typed Notarization on Hardhat Chain 31337',
      mission:
        'Constructing a cryptographic takedown claim signed with your Ethereum wallet to legally dispute stolen images and transition on-chain status to CLAIM DISPUTED.',
      substeps: [
        { text: 'EIP-712 structured claim payload generated with on-chain nonce', delaySeconds: 1 },
        { text: 'ECDSA signature verified against claimant Ethereum address', delaySeconds: 4 },
        { text: 'Dispute recorded on FaceProvenanceRegistry (Lifecycle: DISPUTED)', delaySeconds: 8 },
      ],
      realDataLabel: 'On-Chain Dispute',
      realDataValue: 'CLAIM DISPUTED (TX Receipt Sealed)',
    },
    6: {
      num: 6,
      id: 'zk',
      title: 'Groth16 Zero-Knowledge Privacy Vault',
      subtitle: 'zk-SNARK Biometric Proof on bn128 Curve',
      mission:
        'Proving mathematically that your face matches the registered ledger identity without revealing your raw biometric coordinates to anyone on the blockchain.',
      substeps: [
        { text: 'Quantized Poseidon vector commitments compiled for 512-D vector', delaySeconds: 1 },
        { text: 'Groth16 zk-SNARK witness generated via biometric_match.circom', delaySeconds: 4 },
        { text: 'Smart contract verified similarity (0.924 >= 0.680) with zero leaks', delaySeconds: 8 },
      ],
      realDataLabel: 'ZK Verification',
      realDataValue: 'MATCH PROVEN ON-CHAIN (0% Leakage)',
    },
  };

  const currentPhase = phaseData[currentStep] || phaseData[1];

  return (
    <aside
      aria-label="Interactive Autonomous Pipeline Guide"
      className={`fixed bottom-6 right-6 z-50 transition-all duration-300 max-w-lg w-full ${
        isMinimized ? 'translate-y-[calc(100%-54px)]' : 'translate-y-0'
      }`}
    >
      <div className="cyber-glass rounded-2xl border-2 border-cyan-400 shadow-2xl shadow-cyan-500/20 overflow-hidden bg-cyber-bg/95 backdrop-blur-xl">
        {/* Modal Top Header Bar */}
        <div className="p-3.5 px-4 bg-gradient-to-r from-cyan-950/80 via-blue-950/80 to-purple-950/80 border-b border-cyan-500/30 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping shrink-0" />
            <span className="text-xs font-mono font-bold text-cyan-300 tracking-wider uppercase flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-cyan-400 animate-spin" style={{ animationDuration: '6s' }} />
              PIPELINE GUIDE &bull; PHASE {currentStep} OF 6
            </span>
          </div>

          <div className="flex items-center space-x-1.5">
            <span className="text-[11px] font-mono text-cyan-300 bg-cyan-500/20 px-2 py-0.5 rounded border border-cyan-400/40">
              {secondsRemaining}s
            </span>
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1 rounded text-gray-400 hover:text-white hover:bg-white/10 transition-all cursor-pointer"
              title={isMinimized ? 'Expand Guide' : 'Minimize Guide'}
            >
              {isMinimized ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            <button
              onClick={onCloseTour}
              className="p-1 rounded text-red-400 hover:text-red-200 hover:bg-red-500/20 transition-all cursor-pointer"
              title="Close Guide"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Modal Body */}
        {!isMinimized && (
          <div className="p-4 space-y-4 font-mono">
            {/* Phase Title & Target Identity */}
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-white tracking-wide">{currentPhase.title}</h3>
                <p className="text-[11px] text-cyan-300 mt-0.5">{currentPhase.subtitle}</p>
              </div>

              {targetThumbnail && (
                <div className="flex items-center gap-2 shrink-0 bg-black/60 p-1.5 rounded-lg border border-cyan-500/30">
                  <img
                    src={targetThumbnail}
                    alt="Current target"
                    className="w-9 h-9 rounded object-cover border border-cyan-400/40"
                  />
                  <div className="text-[10px]">
                    <div className="text-gray-400">Target:</div>
                    <div className="text-white font-bold truncate max-w-[80px]">{targetLabel}</div>
                  </div>
                </div>
              )}
            </div>

            {/* Plain English Mission Card */}
            <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-xs text-gray-200 leading-relaxed flex items-start gap-2.5">
              <Zap className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <span>{currentPhase.mission}</span>
            </div>

            {/* Animated Sub-Steps Checklist */}
            <div className="space-y-2 bg-black/40 p-3 rounded-xl border border-cyber-border/40 text-xs">
              <div className="text-[10px] text-gray-400 uppercase tracking-widest font-bold flex items-center gap-1.5 mb-1.5">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" /> Real-time Execution Sub-Steps
              </div>

              {currentPhase.substeps.map((sub, idx) => {
                const isCompleted = elapsed >= sub.delaySeconds;
                const isCurrent = !isCompleted && (idx === 0 || elapsed >= currentPhase.substeps[idx - 1]?.delaySeconds);

                return (
                  <div
                    key={idx}
                    className={`flex items-start gap-2 text-xs transition-all duration-300 ${
                      isCompleted
                        ? 'text-emerald-300'
                        : isCurrent
                        ? 'text-cyan-200 animate-pulse'
                        : 'text-gray-400'
                    }`}
                  >
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-gray-600 flex items-center justify-center text-[9px] shrink-0 mt-0.5">
                        {idx + 1}
                      </div>
                    )}
                    <span className="leading-snug">{sub.text}</span>
                  </div>
                );
              })}
            </div>

            {/* Real Data Highlight */}
            {currentPhase.realDataValue && (
              <div className="p-2.5 bg-black/60 rounded-lg border border-cyan-500/40 flex items-center justify-between text-xs">
                <span className="text-gray-400">{currentPhase.realDataLabel}:</span>
                <span className="text-cyan-300 font-bold">{currentPhase.realDataValue}</span>
              </div>
            )}

            {/* 12s Countdown Visual Progress Bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-[10px] text-gray-400">
                <span>Phase Progress ({elapsed}s / {totalDurationSeconds}s)</span>
                <span className="text-cyan-300 font-bold">Auto-advancing in {secondsRemaining}s</span>
              </div>
              <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 transition-all duration-1000 ease-linear"
                  style={{
                    width: `${((totalDurationSeconds - secondsRemaining) / totalDurationSeconds) * 100}%`,
                  }}
                />
              </div>
            </div>

            {/* Interactive Quick Tour Controls */}
            <div className="flex items-center justify-between pt-1 text-xs">
              <div className="flex items-center gap-2">
                <button
                  onClick={onPrevPhase}
                  disabled={currentStep === 1}
                  className="px-2.5 py-1 bg-cyber-surface border border-cyber-border/40 text-gray-300 hover:text-white rounded disabled:opacity-30 cursor-pointer"
                >
                  ⏮ Prev
                </button>
                <button
                  onClick={onTogglePause}
                  className="px-3 py-1 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/50 rounded transition-all cursor-pointer"
                >
                  {isPaused ? '▶ Resume' : '⏸ Pause'}
                </button>
              </div>

              <button
                onClick={onNextPhase}
                className="px-3.5 py-1 bg-cyan-500/30 hover:bg-cyan-500/40 text-cyan-200 border border-cyan-400/60 rounded flex items-center gap-1 transition-all cursor-pointer font-bold"
              >
                {currentStep < 6 ? 'Next Phase ⏭' : 'Finish Tour ✓'}
              </button>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};
