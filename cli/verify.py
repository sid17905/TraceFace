import logging

import httpx
from eth_abi import decode

from src.blockchain.client import BlockchainClient
from src.config import settings
from src.crypto.merkle import build_provenance_merkle_tree

logger = logging.getLogger(__name__)

async def verify_hash(tx_hash: str) -> tuple[bool, str]:
    """
    1. Fetches the transaction from the blockchain
    2. Parses the IPFS CID
    3. Fetches the JSON from IPFS
    4. Computes the Merkle Hash of the IPFS JSON
    5. Compares it to the Hash on the blockchain
    """
    
    # Initialize blockchain client
    blockchain = BlockchainClient()
    
    try:
        # We need the transaction receipt to get the logs
        receipt = blockchain.w3.eth.get_transaction_receipt(tx_hash)
    except Exception as e:  # noqa: BLE001
        return False, f"Could not find transaction on blockchain: {e}"
        
    if not receipt or not receipt.logs:
        return False, "Transaction has no logs or was not found."

    # Parse the ProvenanceRegistered event
    event_signature = blockchain.w3.keccak(text="ProvenanceRegistered(bytes32,string,bytes32,address,uint64)").hex()
    
    target_log = None
    for log in receipt.logs:
        if log.topics and log.topics[0].hex() == event_signature:
            target_log = log
            break
            
    if not target_log:
        return False, "ProvenanceRegistered event not found in transaction logs."

    # Decode the unindexed data
    unindexed_data = target_log.data
    try:
        decoded_data = decode(['string', 'uint64'], unindexed_data)
        ipfs_cid = decoded_data[0]
        on_chain_merkle_root = target_log.topics[1].hex()
    except Exception as e:  # noqa: BLE001
        return False, f"Failed to decode blockchain event data: {e}"

    if not ipfs_cid:
        return False, "No IPFS CID found in the blockchain record."

    # Fetch the payload from IPFS
    gateway_url = settings.ipfs_gateway
    if not gateway_url.endswith("/"):
        gateway_url += "/"
        
    url = f"{gateway_url}{ipfs_cid}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=15.0)
            response.raise_for_status()
            ipfs_payload = response.json()
    except Exception as e:  # noqa: BLE001
        return False, f"Failed to fetch artifact from IPFS ({ipfs_cid}): {e}"
        
    # Extract the hashes from the payload
    merkle_data = ipfs_payload.get("cryptographic_merkle", {})
    source_image_hash = merkle_data.get("leaf_source_image", "")
    face_embedding_hash = merkle_data.get("leaf_face_embedding", "")
    social_post_hash = merkle_data.get("leaf_social_post", "")
    target_media_hash = merkle_data.get("leaf_target_media", "")

    # Re-calculate the Merkle Tree of the IPFS payload
    recomputed_tree = build_provenance_merkle_tree(
        source_image_hash=source_image_hash,
        face_embedding_hash=face_embedding_hash,
        social_post_hash=social_post_hash,
        target_media_hash=target_media_hash
    )
    recomputed_root = recomputed_tree.merkle_root
    
    # Normalize hex prefix
    if not on_chain_merkle_root.startswith("0x"):
        on_chain_merkle_root = "0x" + on_chain_merkle_root
    
    # Compare
    if recomputed_root.lower() == on_chain_merkle_root.lower():
        return True, ""
    else:
        return False, f"Hash mismatch!\nOn-Chain: {on_chain_merkle_root}\nRecomputed: {recomputed_root}"
