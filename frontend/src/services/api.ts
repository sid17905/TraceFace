/**
 * TraceFace API Service Layer
 */

import {
  FaceScanOutput,
  ScanResponse,
  StageEvent,
  PropagationGraph,
  VerifyResponse,
  ZkProveResponse,
  EIP712TypedData,
  TakedownReceipt,
  OriginNode,
} from '../types';

const API_BASE = '/api/v1';

export class TraceFaceApi {
  /**
   * Health & Capability probe
   */
  static async checkHealth(): Promise<{
    status: string;
    version: string;
    vision_loaded: boolean;
    blockchain_connected: boolean;
    contract_deployed: boolean;
  }> {
    try {
      const res = await fetch('/health');
      if (!res.ok) throw new Error(`Health probe failed: ${res.statusText}`);
      return await res.json();
    } catch {
      return {
        status: 'simulated',
        version: '1.0.0-web',
        vision_loaded: true,
        blockchain_connected: false,
        contract_deployed: true,
      };
    }
  }

  /**
   * Upload an image file for biometric scanning + provenance launching
   */
  static async uploadScan(file: File, runOsint: boolean = true): Promise<ScanResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/scan/upload?run_osint=${runOsint}`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      // Surface the real backend error (e.g. ERR_NO_FACE_DETECTED, unsupported
      // media) to the caller instead of masking it with fabricated scan data.
      throw new Error(err.detail || `Biometric scan failed (HTTP ${res.status})`);
    }

    return await res.json();
  }

  /**
   * Scan an image by public URL
   */
  static async scanByUrl(imageUrl: string, runOsint: boolean = true): Promise<ScanResponse> {
    const res = await fetch(`${API_BASE}/scan/url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_url: imageUrl, run_osint: runOsint }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `URL scan failed (HTTP ${res.status})`);
    }

    return await res.json();
  }

  /**
   * Subscribe to Server-Sent Events (SSE) for real-time OSINT crawl & Merkle sealing updates
   */
  static streamScanEvents(
    jobId: string,
    onEvent: (event: StageEvent) => void,
    onComplete?: () => void,
    onError?: (err: any) => void
  ): () => void {
    const eventSource = new EventSource(`${API_BASE}/scan/stream/${jobId}`);

    eventSource.addEventListener('stage', (e) => {
      try {
        const payload = JSON.parse(e.data);
        onEvent(payload);
      } catch (err) {
        console.error('Failed to parse SSE stage event:', err);
      }
    });

    eventSource.addEventListener('end', () => {
      if (onComplete) onComplete();
      eventSource.close();
    });

    eventSource.onerror = (err) => {
      console.warn('SSE stream disconnected, switching to simulated progression:', err);
      eventSource.close();
      if (onError) onError(err);
    };

    return () => {
      eventSource.close();
    };
  }

  /**
   * Audit zero-tamper provenance record against EVM ledger & 4-leaf Merkle root
   */
  static async verifyRecord(recordHash: string, simulateTamper: boolean = false): Promise<VerifyResponse> {
    const res = await fetch(
      `${API_BASE}/verify/${encodeURIComponent(recordHash)}?simulate_tamper=${simulateTamper}`
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Verification failed (HTTP ${res.status})`);
    }
    return await res.json();
  }

  /**
   * Temporal DAG propagation reconstruction & Root-Zero discovery
   */
  static async propagateGraph(
    nodes: OriginNode[],
    maxHammingDistance: number = 12,
    includeMermaid: boolean = false
  ): Promise<{ graph: PropagationGraph; mermaid?: string }> {
    const res = await fetch(`${API_BASE}/graph/propagate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nodes,
        max_hamming_distance: maxHammingDistance,
        include_mermaid: includeMermaid,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Graph propagation failed (HTTP ${res.status})`);
    }
    return await res.json();
  }

  /**
   * Generate Groth16 biometric match proof
   */
  static async zkProve(
    queryVector: number[],
    ledgerVector: number[],
    threshold: number = 0.68
  ): Promise<ZkProveResponse> {
    const res = await fetch(`${API_BASE}/zk/prove`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query_vector: queryVector,
        ledger_vector: ledgerVector,
        threshold,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `ZK proof generation failed (HTTP ${res.status})`);
    }
    return await res.json();
  }

  /**
   * Verify Groth16 proof
   */
  static async zkVerify(proof: any, publicSignals: string[]): Promise<{ is_valid: boolean }> {
    const res = await fetch(`${API_BASE}/zk/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ proof, publicSignals }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `ZK verification failed (HTTP ${res.status})`);
    }
    return await res.json();
  }

  /**
   * Fetch EIP-712 typed data payload for wallet signing
   */
  static async getTypedData(
    recordHash: string,
    claimant: string,
    reasonCode: number = 1,
    evidenceCid: string = ''
  ): Promise<{
    typed_data: EIP712TypedData;
    nonce: number;
    deadline: number;
    chain_id: number;
    verifying_contract: string;
  }> {
    const res = await fetch(`${API_BASE}/takedown/typed-data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        record_hash: recordHash,
        claimant,
        reason_code: reasonCode,
        evidence_ipfs_cid: evidenceCid,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Failed to generate EIP-712 payload (HTTP ${res.status})`);
    }
    return await res.json();
  }

  /**
   * Submit signed takedown dispute to EVM registry
   */
  static async submitTakedown(params: {
    record_hash: string;
    claimant?: string;
    reason_code: number;
    evidence_ipfs_cid?: string;
    signature?: string;
    deadline?: number;
  }): Promise<TakedownReceipt> {
    const res = await fetch(`${API_BASE}/takedown/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Takedown submission failed (HTTP ${res.status})`);
    }
    return await res.json();
  }

  static async getJobGraph(jobId: string): Promise<{
    job_id: string;
    graph: PropagationGraph;
    nodes_count: number;
    edges_count: number;
  }> {
    const res = await fetch(`${API_BASE}/graph/job/${jobId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Failed to load graph (HTTP ${res.status})`);
    }
    return await res.json();
  }

  static async findSimilarNodes(phash: string, maxHamming: number = 12): Promise<{
    query_phash: string;
    max_hamming_distance: number;
    matching_nodes: OriginNode[];
    count: number;
  }> {
    const res = await fetch(`${API_BASE}/graph/similar/${phash}?max_hamming=${maxHamming}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Failed to find similar nodes (HTTP ${res.status})`);
    }
    return await res.json();
  }
}
