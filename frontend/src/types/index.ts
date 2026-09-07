/**
 * TraceFace Forensic Platform Type Definitions
 */

export interface BoundingBox {
  x?: number;
  y?: number;
  w?: number;
  h?: number;
  x_min?: number;
  y_min?: number;
  x_max?: number;
  y_max?: number;
  landmarks_5pt?: any[];
}

export interface LandmarkPoint {
  x: number;
  y: number;
}

export interface RetinaFaceLandmarks {
  left_eye?: LandmarkPoint;
  right_eye?: LandmarkPoint;
  nose_tip?: LandmarkPoint;
  mouth_left?: LandmarkPoint;
  mouth_right?: LandmarkPoint;
}

export interface QualityMetrics {
  confidence_score: number;
  laplacian_blur_score: number;
  deepfake_score?: number;
  is_deepfake?: boolean;
  is_blurry?: boolean;
  is_genuine_liveness?: boolean;
}

export interface FaceScanOutput {
  scan_id: string;
  image_hash_sha256: string;
  embedding_hash_keccak256: string;
  perceptual_hash_phash: string;
  bounding_box: BoundingBox;
  retinaface_landmarks?: RetinaFaceLandmarks;
  quality_metrics: QualityMetrics;
  embedding_vector?: number[];
  timestamp_utc?: string;
  source_image_path?: string;
}

export interface ScanResponse {
  job_id: string;
  scan: FaceScanOutput;
  osint_started: boolean;
}

export interface StageEvent {
  job_id: string;
  stage: string;
  status: 'started' | 'progress' | 'done' | 'error' | 'final';
  message: string;
  data?: any;
  ts: number;
}

export interface OriginNode {
  node_id: string;
  platform: 'twitter' | 'reddit' | 'instagram' | 'google_lens' | 'facebook' | 'web' | 'youtube' | 'tiktok' | string;
  timestamp: number;
  phash: string;
  similarity_score?: number;
  laplacian_score: number;
  post_url: string;
  author?: string;
  author_handle?: string;
  thumbnail?: string;
  is_root_zero?: boolean;
  timestamp_utc?: string;
}

export interface PropagationEdge {
  source_id: string;
  target_id: string;
  time_delta_seconds: number;
  hamming_distance: number;
  laplacian_decay: number;
}

export interface PropagationGraph {
  nodes: OriginNode[];
  edges: PropagationEdge[];
  root_zero_id: string;
  total_hops: number;
}

export interface MerkleLeaves {
  leaf_0_source_sha256: string;
  leaf_1_biometric_keccak: string;
  leaf_2_social_hash: string;
  leaf_3_target_sha256: string;
}

export interface VerifyResponse {
  is_authentic: boolean;
  status: 'AUTHENTIC' | 'TAMPER_DETECTED' | 'DISPUTED' | 'REVOKED' | 'NOT_FOUND_ON_CHAIN';
  status_badge: string;
  record_hash: string;
  on_chain_exists: boolean;
  on_chain_cid: string;
  on_chain_vector_hash: string;
  on_chain_timestamp: number;
  on_chain_registrant: string;
  recalculated_merkle_root: string;
  leaves_breakdown: Record<string, string>;
  tamper_details?: string;
  social_metadata?: any;
  biometric_similarity?: number;
  dispute_info?: any;
}

export interface ZkProofPayload {
  pi_a: string[];
  pi_b: string[][];
  pi_c: string[];
  protocol: string;
  curve: string;
}

export interface ZkProveResponse {
  proof: ZkProofPayload;
  publicSignals: string[];
  is_valid_match: boolean;
  cosine_similarity: number;
  threshold_enforced: number;
  scaled_dot_product: number;
  scaled_threshold: number;
  query_commitment: string;
  ledger_commitment: string;
}

export interface EIP712TypedData {
  types: {
    EIP712Domain: Array<{ name: string; type: string }>;
    TakedownClaim: Array<{ name: string; type: string }>;
  };
  primaryType: string;
  domain: {
    name: string;
    version: string;
    chainId: number;
    verifyingContract: string;
  };
  message: {
    recordHash: string;
    claimant: string;
    reasonCode: number;
    evidenceIpfsCid: string;
    nonce: number;
    deadline: number;
  };
}

export interface TakedownReceipt {
  status: string;
  tx_hash?: string;
  record_hash: string;
  claimant: string;
  reason_code: number;
  evidence_cid: string;
  new_record_status: string;
  block_number?: number;
  gas_used?: number;
  recovered_signer?: string;
}
