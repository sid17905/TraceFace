from __future__ import annotations

from typing import Any

from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3


def build_takedown_claim_typed_data(
    record_hash: str,
    claimant: str,
    reason_code: int,
    evidence_ipfs_cid: str,
    nonce: int,
    deadline: int,
    chain_id: int,
    contract_address: str,
) -> dict[str, Any]:
    clean_record = record_hash if record_hash.startswith("0x") else f"0x{record_hash}"
    clean_record_bytes = bytes.fromhex(clean_record.removeprefix("0x").zfill(64)[:64])
    checksum_claimant = Web3.to_checksum_address(claimant)
    checksum_contract = Web3.to_checksum_address(contract_address)

    return {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "TakedownClaim": [
                {"name": "recordHash", "type": "bytes32"},
                {"name": "claimant", "type": "address"},
                {"name": "reasonCode", "type": "uint8"},
                {"name": "evidenceIpfsCid", "type": "string"},
                {"name": "nonce", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
            ],
        },
        "primaryType": "TakedownClaim",
        "domain": {
            "name": "TraceFace Provenance Registry",
            "version": "1",
            "chainId": int(chain_id),
            "verifyingContract": checksum_contract,
        },
        "message": {
            "recordHash": clean_record_bytes,
            "claimant": checksum_claimant,
            "reasonCode": int(reason_code),
            "evidenceIpfsCid": str(evidence_ipfs_cid),
            "nonce": int(nonce),
            "deadline": int(deadline),
        },
    }


def sign_takedown_claim(
    private_key: str,
    record_hash: str,
    reason_code: int,
    evidence_ipfs_cid: str,
    nonce: int,
    deadline: int,
    chain_id: int,
    contract_address: str,
) -> tuple[str, str, dict[str, Any]]:
    account = Account.from_key(private_key)
    claimant = account.address
    typed_data = build_takedown_claim_typed_data(
        record_hash=record_hash,
        claimant=claimant,
        reason_code=reason_code,
        evidence_ipfs_cid=evidence_ipfs_cid,
        nonce=nonce,
        deadline=deadline,
        chain_id=chain_id,
        contract_address=contract_address,
    )
    encoded = encode_typed_data(full_message=typed_data)
    signed = Account.sign_message(encoded, private_key=private_key)
    sig_hex = signed.signature.hex()
    if not sig_hex.startswith("0x"):
        sig_hex = f"0x{sig_hex}"
    return sig_hex, claimant, typed_data


def recover_takedown_claimant(typed_data: dict[str, Any], signature: str) -> str:
    encoded = encode_typed_data(full_message=typed_data)
    recovered = Account.recover_message(encoded, signature=signature)
    return Web3.to_checksum_address(recovered)
