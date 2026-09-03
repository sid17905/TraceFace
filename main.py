import hashlib
import json
import logging
import sys

import cv2
import numpy as np
from rich.console import Console

from src.blockchain.client import BlockchainClient
from src.crypto.merkle import build_provenance_merkle_tree
from src.osint.dispatcher import run_osint_search
from src.pipeline.orchestrator import VisionPipeline
from src.storage.ipfs_client import IPFSClient
from src.vision.matcher import compute_cosine_similarity

# Suppress loud third-party logs
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("web3").setLevel(logging.WARNING)

from cli.ui import (
    print_error,
    print_evidence_table,
    print_phase_header,
    print_success,
    simulate_radar_scan,
)

console = Console()

def run_integration_pipeline(target_image_path: str, target_image_url: str | None = None):
    print_phase_header("Initializing Vision Pipeline & Liveness Check...")
    
    with console.status("[cyan]Extracting embedding and verifying liveness...[/cyan]"):
        vision = VisionPipeline()
        try:
            vision_result = vision.process_query_image(target_image_path)
        except ValueError as e:
            print_error(f"Pipeline Aborted: {e}")
            sys.exit(1)
            
        if not vision_result:
            print_error("Pipeline Aborted: Vision processing failed.")
            sys.exit(1)
            
        query_embedding = vision_result.embedding_vector
        target_media_sha256 = vision_result.image_hash_sha256
        scan_id = vision_result.scan_id
    
    print_success("Vision Processing Complete! Liveness Verified. Face embedding extracted.")
    
    print_phase_header("Launching Multi-Engine OSINT Reverse Search...")
    
    def matcher_callback(anchor_emb: list[float], candidate_bytes: bytes) -> float:
        np_arr = np.frombuffer(candidate_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            return 0.0
            
        is_deepfake, _ = vision.liveness.analyze_liveness(img)
        if is_deepfake:
            return 0.0
            
        try:
            det = vision.detector.detect_face(img)
            cand_emb = vision.embedder.get_embedding(img, det["landmarks"])
            return float(compute_cosine_similarity(np.array(anchor_emb), cand_emb))
        except Exception:  # noqa: BLE001
            return 0.0

    # Start the ASCII biometric scan animation!
    simulate_radar_scan()

    with console.status("[cyan]Crawling OSINT engines and filtering identities...[/cyan]"):
        try:
            osint_result = run_osint_search(
                query_scan_id=scan_id,
                image_url=target_image_url,
                image_path=target_image_path,
                query_embedding=query_embedding,
                matcher=matcher_callback,
                strict=True
            )
        except Exception as e:  # noqa: BLE001
            print_error(f"OSINT Engine Failed: {e}")
            sys.exit(1)
    
    if not osint_result.has_verified_match:
        console.print("\n[bold yellow]Pipeline Finished:[/bold yellow] OSINT found no authentic matches across the web.")
        sys.exit(0)
        
    match = osint_result.top_verified_match
    assert match is not None
    
    print_evidence_table([match])
    
    print_phase_header("Anchoring Provenance to Web3 Blockchain...")
    
    with console.status("[cyan]Pinning artifacts to IPFS and signing Ethereum TX...[/cyan]"):
        ipfs = IPFSClient()
        blockchain = BlockchainClient()
        
        social_data = match.to_dict()
        biometric_data = social_data.pop("biometric_verification")
        
        import uuid
        social_data["_nonce"] = str(uuid.uuid4())
        social_post_hash = hashlib.sha256(json.dumps(social_data, sort_keys=True).encode()).hexdigest()
        
        merkle_result = build_provenance_merkle_tree(
            source_image_hash=target_media_sha256,
            face_embedding_hash=vision_result.embedding_hash_keccak256,
            social_post_hash=social_post_hash,
            target_media_hash=match.target_media_sha256
        )
        root_hash = merkle_result.merkle_root
        
        payload = {
            "social_provenance": social_data,
            "biometric_verification": biometric_data,
            "cryptographic_merkle": merkle_result.to_dict()
        }
        
        cid = ipfs.pin_json(payload)
        
        tx_receipt = blockchain.register_provenance(
            record_hash=root_hash,
            ipfs_cid=cid,
            face_vector_hash=target_media_sha256
        )
    
    print_success("Immutable Payload Pinned to IPFS!")
    console.print(f"  └─ CID: {cid}")
    print_success("Cryptographic Proof Anchored to Ethereum!")
    console.print(f"  └─ TX Hash: {tx_receipt['tx_hash']}")
    
    console.print("\n[bold magenta]=================================================[/bold magenta]")
    console.print("[bold green]   TraceFace Pipeline Executed Successfully!   [/bold green]")
    console.print("[bold magenta]=================================================[/bold magenta]")
    
    return tx_receipt

if __name__ == "__main__":
    import cli.main
    cli.main.app()
