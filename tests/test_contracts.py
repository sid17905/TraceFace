import pytest
from unittest.mock import MagicMock
from src.storage.ipfs_client import IPFSClient
from src.blockchain.client import BlockchainClient
from src.blockchain.verifier import ZeroTamperVerifier
from src.crypto.merkle import build_provenance_merkle_tree


def test_ipfs_client_local_pin_and_fetch():
    client = IPFSClient()
    payload = {
        "version": "1.0.0-TraceFace",
        "sample": "data",
        "nested": {"key": 123},
    }

    cid = client.pin_json(payload)
    assert cid.startswith("bafybei")

    fetched = client.fetch_json(cid)
    assert fetched["version"] == "1.0.0-TraceFace"
    assert fetched["sample"] == "data"
    assert fetched["nested"]["key"] == 123


def test_zero_tamper_verifier_authentic():
    leaf_src = "0x" + "a" * 64
    leaf_emb = "0x" + "b" * 64
    leaf_soc = "0x" + "c" * 64
    leaf_tgt = "0x" + "d" * 64

    tree = build_provenance_merkle_tree(leaf_src, leaf_emb, leaf_soc, leaf_tgt)
    record_hash = tree.merkle_root

    mock_ipfs = IPFSClient()
    payload = {
        "version": "1.0.0-TraceFace",
        "cryptographic_merkle": tree.to_dict(),
        "social_provenance": {
            "platform": "Twitter/X",
            "post_url": "https://x.com/sample/status/123",
            "author_handle": "@sample",
        },
        "biometric_evidence": {"cosine_similarity": 0.91},
    }
    cid = mock_ipfs.pin_json(payload)

    # Mock blockchain client response
    mock_chain = MagicMock(spec=BlockchainClient)
    mock_chain.get_provenance.return_value = {
        "exists": True,
        "record_hash": record_hash,
        "ipfs_cid": cid,
        "face_vector_hash": leaf_emb,
        "timestamp": 1725280000,
        "registrant": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    }

    verifier = ZeroTamperVerifier(blockchain_client=mock_chain, ipfs_client=mock_ipfs)

    result = verifier.verify_by_record_hash(record_hash, simulate_tamper=False)
    assert result.is_authentic is True
    assert result.status == "AUTHENTIC"
    assert result.biometric_similarity == 0.91
    assert result.on_chain_registrant == "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"


def test_zero_tamper_verifier_detects_tampering():
    leaf_src = "0x" + "a" * 64
    leaf_emb = "0x" + "b" * 64
    leaf_soc = "0x" + "c" * 64
    leaf_tgt = "0x" + "d" * 64

    tree = build_provenance_merkle_tree(leaf_src, leaf_emb, leaf_soc, leaf_tgt)
    record_hash = tree.merkle_root

    mock_ipfs = IPFSClient()
    payload = {
        "version": "1.0.0-TraceFace",
        "cryptographic_merkle": tree.to_dict(),
        "social_provenance": {"post_text_sha256": "0x1234"},
        "biometric_evidence": {"cosine_similarity": 0.85},
    }
    cid = mock_ipfs.pin_json(payload)

    mock_chain = MagicMock(spec=BlockchainClient)
    mock_chain.get_provenance.return_value = {
        "exists": True,
        "record_hash": record_hash,
        "ipfs_cid": cid,
        "face_vector_hash": leaf_emb,
        "timestamp": 1725280000,
        "registrant": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    }

    verifier = ZeroTamperVerifier(blockchain_client=mock_chain, ipfs_client=mock_ipfs)

    # When tamper simulation is enabled
    result = verifier.verify_by_record_hash(record_hash, simulate_tamper=True)
    assert result.is_authentic is False
    assert result.status == "TAMPER_DETECTED"
    assert "Mismatch detected" in result.tamper_details
