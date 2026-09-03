from unittest.mock import MagicMock

import numpy as np

from src.analytics.graph_visualizer import render_ascii_timeline, render_mermaid_graph
from src.analytics.origin_graph import build_propagation_graph
from src.blockchain.eip712 import (
    recover_takedown_claimant,
    sign_takedown_claim,
)
from src.blockchain.verifier import ZeroTamperVerifier
from src.crypto.merkle import build_provenance_merkle_tree
from src.crypto.zk_prover import ZkBiometricProver
from src.pipeline.types import OriginNode


def test_e2e_temporal_origin_graph_flow():
    nodes = [
        OriginNode(
            node_id="root_node",
            platform="Twitter/X",
            post_url="https://x.com/creator/1",
            author_handle="@creator",
            timestamp_utc="2026-04-18T10:00:00Z",
            phash="a1b2c3d4e5f60718",
            laplacian_score=160.0,
        ),
        OriginNode(
            node_id="hop_1",
            platform="Reddit",
            post_url="https://reddit.com/r/news/1",
            author_handle="/r/news",
            timestamp_utc="2026-04-18T12:00:00Z",
            phash="a1b2c3d4e5f60719",
            laplacian_score=140.0,
        ),
        OriginNode(
            node_id="hop_2",
            platform="Instagram",
            post_url="https://instagram.com/p/1",
            author_handle="@repost",
            timestamp_utc="2026-04-18T18:00:00Z",
            phash="a1b2c3d4e5f6071f",
            laplacian_score=110.0,
        ),
    ]

    graph = build_propagation_graph(nodes)
    assert graph.root_zero_node_id == "root_node"
    assert len(graph.edges) == 2
    assert graph.edges[0].delta_seconds == 7200.0
    assert graph.edges[0].phash_hamming_distance == 1

    ascii_rep = render_ascii_timeline(graph)
    assert "Origin Root-Zero" in ascii_rep
    assert "Twitter/X (@creator)" in ascii_rep

    mermaid_rep = render_mermaid_graph(graph)
    assert "graph TD" in mermaid_rep
    assert "root_node" in mermaid_rep


def test_e2e_zk_snark_proof_flow():
    np.random.seed(999)
    query_vec = (np.random.randn(512) / np.linalg.norm(np.random.randn(512))).tolist()
    ledger_vec = list(query_vec)

    prover = ZkBiometricProver()
    proof_data = prover.generate_proof(query_vec, ledger_vec, threshold=0.68)

    assert proof_data["is_valid_match"] is True
    assert proof_data["publicSignals"][0] == "1"
    assert prover.verify_proof(proof_data) is True

    _a, _b, _c, inputs = prover.format_for_solidity(proof_data)
    assert inputs[0] == 1


def test_e2e_eip712_takedown_and_audit_flow():
    privkey = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    contract_addr = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

    tree = build_provenance_merkle_tree("0x" + "11" * 32, "0x" + "22" * 32, "0x" + "33" * 32, "0x" + "44" * 32)
    record_hash = tree.merkle_root
    cid = "bafybeic96cdf18205ddf30d4df5c075ebde9b01fb04c5f39065a"

    sig, claimant, typed_data = sign_takedown_claim(
        private_key=privkey,
        record_hash=record_hash,
        reason_code=1,
        evidence_ipfs_cid=cid,
        nonce=0,
        deadline=1900000000,
        chain_id=31337,
        contract_address=contract_addr,
    )
    assert recover_takedown_claimant(typed_data, sig) == claimant

    mock_chain = MagicMock()
    mock_ipfs = MagicMock()

    mock_chain.get_provenance.return_value = {
        "exists": True,
        "ipfs_cid": cid,
        "face_vector_hash": "0x" + "22" * 32,
        "timestamp": 1700000000,
        "registrant": claimant,
    }
    mock_chain._format_bytes32.return_value = bytes.fromhex(record_hash.removeprefix("0x"))

    mock_ipfs.fetch_json.return_value = {
        "cryptographic_merkle": tree.to_dict(),
        "social_provenance": {"author_handle": "@creator"},
    }

    mock_contract = MagicMock()
    mock_chain.contract = mock_contract
    mock_contract.functions.getRecordStatus.return_value.call.return_value = 0
    mock_contract.functions.getDispute.return_value.call.return_value = (
        "0x0000000000000000000000000000000000000000", 0, "", 0, False
    )

    verifier = ZeroTamperVerifier(mock_chain, mock_ipfs)
    audit_active = verifier.verify_by_record_hash(record_hash)
    assert audit_active.is_authentic is True
    assert audit_active.status == "AUTHENTIC"
    assert "[AUTH]" in audit_active.status_badge

    mock_contract.functions.getRecordStatus.return_value.call.return_value = 1
    mock_contract.functions.getDispute.return_value.call.return_value = (
        claimant, 1, cid, 1700001000, False
    )
    audit_disputed = verifier.verify_by_record_hash(record_hash)
    assert audit_disputed.status == "DISPUTED"
    assert "[DISPUTED]" in audit_disputed.status_badge

    mock_contract.functions.getRecordStatus.return_value.call.return_value = 2
    audit_revoked = verifier.verify_by_record_hash(record_hash)
    assert audit_revoked.is_authentic is False
    assert audit_revoked.status == "REVOKED"
    assert "[REVOKED]" in audit_revoked.status_badge
