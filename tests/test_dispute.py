from unittest.mock import MagicMock

from eth_account import Account

from src.blockchain.dispute_client import STATUS_MAP, STATUS_TO_INT
from src.blockchain.eip712 import (
    recover_takedown_claimant,
    sign_takedown_claim,
)
from src.blockchain.verifier import ZeroTamperVerifier


def test_eip712_sign_and_recover():
    privkey = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    account = Account.from_key(privkey)
    contract_addr = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
    record_hash = "0x" + "aa" * 32
    cid = "bafybeic96cdf18205ddf30d4df5c075ebde9b01fb04c5f39065a"

    sig, claimant, typed_data = sign_takedown_claim(
        private_key=privkey,
        record_hash=record_hash,
        reason_code=1,
        evidence_ipfs_cid=cid,
        nonce=0,
        deadline=1800000000,
        chain_id=31337,
        contract_address=contract_addr,
    )

    assert claimant == account.address
    assert sig.startswith("0x")

    recovered = recover_takedown_claimant(typed_data, sig)
    assert recovered.lower() == account.address.lower()


def test_status_mapping():
    assert STATUS_MAP[0] == "ACTIVE"
    assert STATUS_MAP[1] == "DISPUTED"
    assert STATUS_MAP[2] == "REVOKED"
    assert STATUS_MAP[3] == "CONFIRMED"
    assert STATUS_TO_INT["ACTIVE"] == 0
    assert STATUS_TO_INT["DISPUTED"] == 1


def test_verifier_badges_with_disputes():
    mock_chain = MagicMock()
    mock_ipfs = MagicMock()

    from src.crypto.merkle import build_provenance_merkle_tree

    tree = build_provenance_merkle_tree("0x" + "00" * 32, "0x" + "00" * 32, "0x" + "00" * 32, "0x" + "00" * 32)
    record_hash = tree.merkle_root
    mock_chain.get_provenance.return_value = {
        "exists": True,
        "ipfs_cid": "cid123",
        "face_vector_hash": "0x" + "22" * 32,
        "timestamp": 123456789,
        "registrant": "0x" + "33" * 20,
    }
    mock_chain._format_bytes32.return_value = b"\x11" * 32

    mock_ipfs.fetch_json.return_value = {
        "cryptographic_merkle": {
            "merkle_root": record_hash,
            "leaf_source_image": "0x" + "00" * 32,
            "leaf_face_embedding": "0x" + "00" * 32,
            "leaf_social_post": "0x" + "00" * 32,
            "leaf_target_media": "0x" + "00" * 32,
        },
        "social_provenance": {"author_handle": "@test"},
    }

    mock_contract = MagicMock()
    mock_chain.contract = mock_contract
    mock_contract.functions.getRecordStatus.return_value.call.return_value = 1
    mock_contract.functions.getDispute.return_value.call.return_value = (
        "0x" + "44" * 20,
        1,
        "evidence_cid",
        123456,
        False,
    )

    verifier = ZeroTamperVerifier(mock_chain, mock_ipfs)
    res = verifier.verify_by_record_hash(record_hash)

    assert res.status == "DISPUTED"
    assert "DISPUTED" in res.status_badge
    assert res.dispute_info is not None

    mock_contract.functions.getRecordStatus.return_value.call.return_value = 2
    res_revoked = verifier.verify_by_record_hash(record_hash)
    assert res_revoked.status == "REVOKED"
    assert "REVOKED" in res_revoked.status_badge
    assert res_revoked.is_authentic is False
