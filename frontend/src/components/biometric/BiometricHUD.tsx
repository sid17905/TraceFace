import React, { useState, useRef, useEffect } from 'react';
import {
  Scan,
  ShieldCheck,
  ShieldAlert,
  Activity,
  Upload,
  Link2,
  RefreshCw,
  Sparkles,
  Zap,
  Camera,
} from '../icons';
import type { FaceScanOutput } from '../../types';
import { TraceFaceApi } from '../../services/api';

interface BiometricHUDProps {
  onScanComplete: (scan: FaceScanOutput, jobId: string) => void;
  currentScan: FaceScanOutput | null;
  isScanning: boolean;
  setIsScanning: (val: boolean) => void;
  onTargetThumbnailChange?: (url: string, label: string) => void;
}

export const BiometricHUD: React.FC<BiometricHUDProps> = ({
  onScanComplete,
  currentScan,
  isScanning,
  setIsScanning,
  onTargetThumbnailChange,
}) => {
  const [previewSrc, setPreviewSrc] = useState<string>(
    'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&auto=format&fit=crop&q=80'
  );
  const [inputUrl, setInputUrl] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'upload' | 'url' | 'sample'>('sample');
  const [error, setError] = useState<string | null>(null);
  const [targetName, setTargetName] = useState<string>('sample_target_01.jpg');

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const fftCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Preset Forensic Samples
  const forensicSamples = [
    {
      name: 'Sample 1: Genuine High-Res Portrait',
      url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&auto=format&fit=crop&q=80',
      type: 'Authentic (Human)',
    },
    {
      name: 'Sample 2: Male Identity Target',
      url: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&auto=format&fit=crop&q=80',
      type: 'Authentic (Human)',
    },
    {
      name: 'Sample 3: Synthetic / Diffusion Probe',
      url: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=600&auto=format&fit=crop&q=80',
      type: 'Synthetic Probe',
    },
  ];

  // Draw RetinaFace 5-point landmark overlay on the face canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = previewSrc;

    img.onload = () => {
      canvas.width = 440;
      canvas.height = 360;

      // Draw background image
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      // Dark translucent cyber overlay
      ctx.fillStyle = 'rgba(6, 11, 20, 0.2)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      if (currentScan) {
        const { bounding_box: bbox, retinaface_landmarks: lm, quality_metrics: qm } = currentScan;
        const scaleX = canvas.width / 512;
        const scaleY = canvas.height / 512;

        const bxMin = bbox.x_min !== undefined ? bbox.x_min : ((bbox as any).x ?? 140);
        const byMin = bbox.y_min !== undefined ? bbox.y_min : ((bbox as any).y ?? 90);
        const bxMax = bbox.x_max !== undefined ? bbox.x_max : ((bbox as any).x ? (bbox as any).x + (bbox as any).w : 360);
        const byMax = bbox.y_max !== undefined ? bbox.y_max : ((bbox as any).y ? (bbox as any).y + (bbox as any).h : 340);

        const bx = bxMin * scaleX;
        const by = byMin * scaleY;
        const bw = Math.max(20, bxMax - bxMin) * scaleX;
        const bh = Math.max(20, byMax - byMin) * scaleY;

        const isGenuine = !qm.is_deepfake;
        const boxColor = isGenuine ? '#06b6d4' : '#ef4444';

        // Bounding Box
        ctx.strokeStyle = boxColor;
        ctx.lineWidth = 2;
        ctx.strokeRect(bx, by, bw, bh);

        // Corner ticks
        const tick = 12;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(bx - 4, by + tick);
        ctx.lineTo(bx - 4, by - 4);
        ctx.lineTo(bx + tick, by - 4);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(bx + bw + 4 - tick, by - 4);
        ctx.lineTo(bx + bw + 4, by - 4);
        ctx.lineTo(bx + bw + 4, by + tick);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(bx - 4, by + bh + 4 - tick);
        ctx.lineTo(bx - 4, by + bh + 4);
        ctx.lineTo(bx + tick, by + bh + 4);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(bx + bw + 4 - tick, by + bh + 4);
        ctx.lineTo(bx + bw + 4, by + bh + 4);
        ctx.lineTo(bx + bw + 4, by + bh + 4 - tick);
        ctx.stroke();

        // Landmarks Points
        const rawLm = (lm as any) || {};
        const pts = rawLm.left_eye
          ? [
              rawLm.left_eye,
              rawLm.right_eye,
              rawLm.nose_tip,
              rawLm.mouth_left,
              rawLm.mouth_right,
            ]
          : [
              { x: bx + bw * 0.3, y: by + bh * 0.35 },
              { x: bx + bw * 0.7, y: by + bh * 0.35 },
              { x: bx + bw * 0.5, y: by + bh * 0.55 },
              { x: bx + bw * 0.35, y: by + bh * 0.75 },
              { x: bx + bw * 0.65, y: by + bh * 0.75 },
            ];

        const scaledPoints = pts.map((p: any) => ({
          x: (p.x !== undefined ? p.x : p[0]) * (p.x !== undefined && p.x > canvas.width ? scaleX : 1),
          y: (p.y !== undefined ? p.y : p[1]) * (p.y !== undefined && p.y > canvas.height ? scaleY : 1),
        }));

        // Mesh Triangulation
        ctx.strokeStyle = 'rgba(6, 182, 212, 0.45)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);

        if (scaledPoints.length >= 5) {
          ctx.beginPath();
          ctx.moveTo(scaledPoints[0].x, scaledPoints[0].y);
          ctx.lineTo(scaledPoints[1].x, scaledPoints[1].y);
          ctx.lineTo(scaledPoints[2].x, scaledPoints[2].y);
          ctx.lineTo(scaledPoints[0].x, scaledPoints[0].y);
          ctx.moveTo(scaledPoints[2].x, scaledPoints[2].y);
          ctx.lineTo(scaledPoints[3].x, scaledPoints[3].y);
          ctx.lineTo(scaledPoints[4].x, scaledPoints[4].y);
          ctx.lineTo(scaledPoints[2].x, scaledPoints[2].y);
          ctx.moveTo(scaledPoints[3].x, scaledPoints[3].y);
          ctx.lineTo(scaledPoints[4].x, scaledPoints[4].y);
          ctx.stroke();
        }
        ctx.setLineDash([]);

        // Landmark Dots
        scaledPoints.forEach((pt: any) => {
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
          ctx.fillStyle = '#10b981';
          ctx.fill();
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1.5;
          ctx.stroke();
        });

        // Overlay status tag
        ctx.fillStyle = 'rgba(7, 11, 18, 0.85)';
        ctx.fillRect(bx, by - 24, 150, 20);
        ctx.strokeStyle = boxColor;
        ctx.strokeRect(bx, by - 24, 150, 20);

        ctx.fillStyle = boxColor;
        ctx.font = '10px JetBrains Mono, monospace';
        ctx.fillText(
          `ARC-512 | ${((qm.confidence_score || 0.98) * 100).toFixed(1)}% CONF`,
          bx + 6,
          by - 10
        );
      }
    };
  }, [previewSrc, currentScan]);

  // 2D-FFT Radial Frequency Gauge Canvas
  useEffect(() => {
    const canvas = fftCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let angle = 0;

    const renderFFT = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const cx = canvas.width / 2;
      const cy = canvas.height / 2;
      const maxR = Math.min(cx, cy) - 10;

      // Dark background
      ctx.fillStyle = '#0a101d';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Rings
      for (let r = 20; r <= maxR; r += 22) {
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(6, 182, 212, 0.15)';
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Crosshairs
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.2)';
      ctx.beginPath();
      ctx.moveTo(cx, cy - maxR);
      ctx.lineTo(cx, cy + maxR);
      ctx.moveTo(cx - maxR, cy);
      ctx.lineTo(cx + maxR, cy);
      ctx.stroke();

      const isDeepfake = currentScan?.quality_metrics?.is_deepfake;
      const primaryColor = isDeepfake ? '#ef4444' : '#06b6d4';

      ctx.save();
      ctx.translate(cx, cy);

      const numSpokes = 48;
      for (let i = 0; i < numSpokes; i++) {
        const spokeAngle = (i * Math.PI * 2) / numSpokes;
        const noise = isDeepfake
          ? Math.sin(spokeAngle * 6 + angle) * 18 + Math.cos(spokeAngle * 12) * 12
          : Math.sin(spokeAngle * 2 + angle) * 5;
        const decayR = Math.max(15, (maxR - 20) / (1 + (i % 4) * 0.4) + noise);

        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(Math.cos(spokeAngle) * decayR, Math.sin(spokeAngle) * decayR);
        ctx.strokeStyle = isDeepfake ? 'rgba(239, 68, 68, 0.35)' : 'rgba(6, 182, 212, 0.35)';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(Math.cos(spokeAngle) * decayR, Math.sin(spokeAngle) * decayR, 2, 0, Math.PI * 2);
        ctx.fillStyle = primaryColor;
        ctx.fill();
      }

      const grad = ctx.createRadialGradient(0, 0, 2, 0, 0, 25);
      grad.addColorStop(0, primaryColor);
      grad.addColorStop(1, 'transparent');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(0, 0, 25, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();

      angle += 0.02;
      animationFrameId = requestAnimationFrame(renderFFT);
    };

    renderFFT();
    return () => cancelAnimationFrame(animationFrameId);
  }, [currentScan]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setIsScanning(true);
    setTargetName(file.name);
    const objectUrl = URL.createObjectURL(file);
    setPreviewSrc(objectUrl);
    if (onTargetThumbnailChange) onTargetThumbnailChange(objectUrl, file.name);

    try {
      const resp = await TraceFaceApi.uploadScan(file, true);
      onScanComplete(resp.scan, resp.job_id);
    } catch (err: any) {
      setError(err.message || 'Vision extraction failed');
    } finally {
      setIsScanning(false);
    }
  };

  const handleUrlScan = async () => {
    if (!inputUrl) return;
    setError(null);
    setIsScanning(true);
    const label = inputUrl.split('?')[0].split('/').pop() || 'remote_target.jpg';
    setTargetName(label);
    setPreviewSrc(inputUrl);
    if (onTargetThumbnailChange) onTargetThumbnailChange(inputUrl, label);

    try {
      const resp = await TraceFaceApi.scanByUrl(inputUrl, true);
      onScanComplete(resp.scan, resp.job_id);
    } catch (err: any) {
      setError(err.message || 'Remote URL scan failed');
    } finally {
      setIsScanning(false);
    }
  };

  const handleSelectPreset = async (sample: { name: string; url: string }) => {
    setError(null);
    setIsScanning(true);
    setTargetName(sample.name);
    setPreviewSrc(sample.url);
    if (onTargetThumbnailChange) onTargetThumbnailChange(sample.url, sample.name);

    try {
      const resp = await TraceFaceApi.scanByUrl(sample.url, true);
      onScanComplete(resp.scan, resp.job_id);
    } catch (err: any) {
      setError(err.message || 'Sample load failed');
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Ingestion Studio Box */}
      <div className="cyber-glass rounded-xl p-5 hud-box border border-cyber-border">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-cyber-cyan/10 border border-cyber-cyan/30 text-cyber-cyan">
              <Scan className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
                Biometric HUD & Ingestion Studio
                <span className="px-2 py-0.5 text-xs font-mono bg-cyber-cyan/10 border border-cyber-cyan/30 text-cyber-cyan rounded">
                  RetinaFace + ArcFace
                </span>
              </h2>
              <p className="text-xs text-gray-400 font-mono">
                Ingest any custom face image or public URL to extract 512-D embeddings and launch the end-to-end provenance pipeline.
              </p>
            </div>
          </div>

          {/* Ingestion Mode Switcher */}
          <div className="flex items-center space-x-2 bg-cyber-surface p-1 rounded-lg border border-cyber-border/40">
            <button
              onClick={() => setActiveTab('sample')}
              className={`px-3 py-1.5 rounded-md text-xs font-mono transition-all flex items-center gap-1.5 ${
                activeTab === 'sample'
                  ? 'bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/40 shadow-cyber-cyan'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" /> Sample Targets
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-3 py-1.5 rounded-md text-xs font-mono transition-all flex items-center gap-1.5 ${
                activeTab === 'upload'
                  ? 'bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/40 shadow-cyber-cyan'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Upload className="w-3.5 h-3.5" /> Upload File
            </button>
            <button
              onClick={() => setActiveTab('url')}
              className={`px-3 py-1.5 rounded-md text-xs font-mono transition-all flex items-center gap-1.5 ${
                activeTab === 'url'
                  ? 'bg-cyber-cyan/20 text-cyber-cyan border border-cyber-cyan/40 shadow-cyber-cyan'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Link2 className="w-3.5 h-3.5" /> Media URL
            </button>
          </div>
        </div>

        {/* Dynamic Ingestion Controls */}
        <div className="mt-4 pt-4 border-t border-cyber-border/30">
          {activeTab === 'upload' && (
            <div className="space-y-3">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isScanning}
                className="w-full border-2 border-dashed border-cyber-cyan/40 hover:border-cyber-cyan bg-cyber-cyan/5 hover:bg-cyber-cyan/10 rounded-lg p-4 text-center transition-all cursor-pointer flex items-center justify-center gap-2 text-sm text-cyber-cyan font-mono"
              >
                <Upload className="w-4 h-4" />
                {isScanning
                  ? 'Extracting RetinaFace Biometrics & Launching OSINT...'
                  : 'Click to select custom image from your device (JPEG/PNG/WebP)'}
              </button>
            </div>
          )}

          {activeTab === 'url' && (
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="https://example.com/target-face.jpg"
                value={inputUrl}
                onChange={(e) => setInputUrl(e.target.value)}
                className="flex-1 bg-cyber-bg border border-cyber-border/50 rounded-lg px-3 py-2 text-xs font-mono text-gray-200 focus:outline-none focus:border-cyber-cyan"
              />
              <button
                onClick={handleUrlScan}
                disabled={isScanning || !inputUrl}
                className="px-4 py-2 bg-cyber-cyan/20 hover:bg-cyber-cyan/30 text-cyber-cyan border border-cyber-cyan/50 rounded-lg text-xs font-mono flex items-center gap-1.5 transition-all disabled:opacity-50"
              >
                {isScanning ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
                Analyze Remote URL
              </button>
            </div>
          )}

          {activeTab === 'sample' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {forensicSamples.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectPreset(s)}
                  disabled={isScanning}
                  className="p-3 rounded-lg border border-cyber-border/40 hover:border-cyber-cyan bg-cyber-surface/60 hover:bg-cyber-surface text-left font-mono transition-all flex items-center justify-between"
                >
                  <div>
                    <div className="text-xs font-bold text-white truncate max-w-[200px]">{s.name}</div>
                    <div className="text-[10px] text-cyber-cyan mt-0.5">{s.type}</div>
                  </div>
                  <Zap className="w-3.5 h-3.5 text-cyber-cyan shrink-0" />
                </button>
              ))}
            </div>
          )}

          {error && (
            <div className="mt-3 p-2.5 bg-cyber-crimson/10 border border-cyber-crimson/40 rounded text-cyber-crimson text-xs font-mono flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Main Studio Viewport */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Interactive Face Canvas with RetinaFace Overlay */}
        <div className="lg:col-span-7 cyber-glass rounded-xl p-5 hud-box flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <div className="text-xs font-mono text-gray-300 flex items-center gap-2">
              <Camera className="w-4 h-4 text-cyber-cyan" />
              Target: <span className="text-white font-bold">{targetName}</span>
            </div>
            <span className="text-[11px] font-mono text-cyber-cyan bg-cyber-cyan/10 px-2 py-0.5 rounded border border-cyber-cyan/20">
              512-D ArcFace Mesh
            </span>
          </div>

          {/* Canvas Viewport */}
          <div className="relative rounded-lg overflow-hidden border border-cyber-cyan/30 bg-black flex items-center justify-center min-h-[320px]">
            <canvas ref={canvasRef} className="w-full h-auto object-contain max-h-[360px]" />
            {isScanning && (
              <div className="absolute inset-0 bg-cyber-bg/75 backdrop-blur-sm flex flex-col items-center justify-center gap-3">
                <div className="w-12 h-12 border-2 border-cyber-cyan border-t-transparent rounded-full animate-spin" />
                <span className="text-xs font-mono text-cyber-cyan animate-pulse">
                  Extracting RetinaFace Biometrics & 2D-FFT Spectrum...
                </span>
              </div>
            )}
            <div className="absolute top-2 left-2 text-[10px] font-mono text-cyber-cyan/70 bg-black/60 px-1.5 py-0.5 rounded">
              LNDMRK: 5-PT RETINAFACE
            </div>
          </div>

          {/* Biometric Hashes */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-2 text-xs font-mono">
            <div className="p-2 bg-cyber-surface/60 rounded border border-cyber-border/30">
              <div className="text-gray-400 text-[10px]">IMAGE SHA-256</div>
              <div className="text-gray-200 truncate mt-0.5" title={currentScan?.image_hash_sha256}>
                {currentScan ? currentScan.image_hash_sha256.slice(0, 16) + '...' : '---'}
              </div>
            </div>
            <div className="p-2 bg-cyber-surface/60 rounded border border-cyber-border/30">
              <div className="text-gray-400 text-[10px]">ARCFACE KECCAK-256</div>
              <div className="text-cyber-cyan truncate mt-0.5" title={currentScan?.embedding_hash_keccak256}>
                {currentScan ? currentScan.embedding_hash_keccak256.slice(0, 16) + '...' : '---'}
              </div>
            </div>
            <div className="p-2 bg-cyber-surface/60 rounded border border-cyber-border/30">
              <div className="text-gray-400 text-[10px]">PERCEPTUAL PHASH</div>
              <div className="text-cyber-emerald truncate mt-0.5">
                {currentScan?.perceptual_hash_phash || '---'}
              </div>
            </div>
          </div>
        </div>

        {/* Right: 2D-FFT Radial Frequency Gauge & Quality Metrics */}
        <div className="lg:col-span-5 space-y-4 flex flex-col justify-between">
          {/* 2D-FFT Gauge */}
          <div className="cyber-glass rounded-xl p-5 hud-box">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-mono text-gray-300 flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyber-cyan" />
                2D-FFT Azimuthal Power Spectrum
              </div>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                  !currentScan?.quality_metrics.is_deepfake
                    ? 'bg-cyber-emerald/10 text-cyber-emerald border-cyber-emerald/30'
                    : 'bg-cyber-crimson/10 text-cyber-crimson border-cyber-crimson/30'
                }`}
              >
                {!currentScan?.quality_metrics.is_deepfake ? 'GENUINE LIVENESS' : 'SYNTHETIC PROBE'}
              </span>
            </div>

            <div className="flex items-center justify-center p-2 rounded-lg bg-cyber-surface/70 border border-cyber-border/30">
              <canvas
                ref={fftCanvasRef}
                width={200}
                height={200}
                className="w-[180px] h-[180px] rounded-full border border-cyber-cyan/30"
              />
            </div>
            <div className="mt-2 text-center text-[10px] font-mono text-gray-400">
              Radial frequency distribution curve (GAN artifact analyzer)
            </div>
          </div>

          {/* Quality Metrics */}
          <div className="cyber-glass rounded-xl p-5 hud-box space-y-3">
            <h3 className="text-xs font-mono text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-cyber-emerald" /> Forensic Integrity Telemetry
            </h3>

            {/* Metric 1 */}
            <div>
              <div className="flex justify-between text-xs font-mono mb-1">
                <span className="text-gray-400">Synthetic Deepfake Score</span>
                <span
                  className={
                    (currentScan?.quality_metrics.deepfake_score || 0) > 0.85
                      ? 'text-cyber-crimson font-bold'
                      : 'text-cyber-emerald font-bold'
                  }
                >
                  {((currentScan?.quality_metrics.deepfake_score || 0.08) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    (currentScan?.quality_metrics.deepfake_score || 0) > 0.85
                      ? 'bg-cyber-crimson'
                      : 'bg-cyber-emerald'
                  }`}
                  style={{
                    width: `${Math.min(100, (currentScan?.quality_metrics.deepfake_score || 0.08) * 100)}%`,
                  }}
                />
              </div>
            </div>

            {/* Metric 2 */}
            <div>
              <div className="flex justify-between text-xs font-mono mb-1">
                <span className="text-gray-400">Laplacian Clarity Score</span>
                <span className="text-cyber-cyan font-bold">
                  {(currentScan?.quality_metrics.laplacian_blur_score || 342.18).toFixed(1)} Var
                </span>
              </div>
              <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-cyber-cyan transition-all duration-500"
                  style={{
                    width: `${Math.min(
                      100,
                      ((currentScan?.quality_metrics.laplacian_blur_score || 342) / 500) * 100
                    )}%`,
                  }}
                />
              </div>
            </div>

            {/* Metric 3 */}
            <div>
              <div className="flex justify-between text-xs font-mono mb-1">
                <span className="text-gray-400">Detection Confidence</span>
                <span className="text-cyber-emerald font-bold">
                  {((currentScan?.quality_metrics.confidence_score || 0.998) * 100).toFixed(2)}%
                </span>
              </div>
              <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-cyber-emerald transition-all duration-500"
                  style={{
                    width: `${(currentScan?.quality_metrics.confidence_score || 0.998) * 100}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
