from __future__ import annotations

import time
from typing import Any

from eth_account import Account
from web3 import Web3

from src.blockchain.client import BlockchainClient
from src.blockchain.eip712 import sign_takedown_claim
from src.config import settings

STATUS_MAP = {
    0: "ACTIVE",
    1: "DISPUTED",
    2: "REVOKED",
    3: "CONFIRMED",
}

STATUS_TO_INT = {
    "ACTIVE": 0,
    "DISPUTED": 1,
    "REVOKED": 2,
    "CONFIRMED": 3,
}


class DisputeClient:
    def __init__(
        self,
        blockchain_client: BlockchainClient | None = None,
        private_key: str | None = None,
    ):
        self.chain = blockchain_client or BlockchainClient()
        self.private_key = private_key or settings.private_key
        if self.private_key:
            self.account = Account.from_key(self.private_key)
        else:
            self.account = None

    def _format_bytes32(self, hex_val: str) -> bytes:
        clean = hex_val.removeprefix("0x")
        clean = clean.zfill(64)[:64]
        return bytes.fromhex(clean)

    def get_record_status(self, record_hash: str) -> str:
        if not self.chain.contract:
            return "UNKNOWN"
        try:
            b32_record = self._format_bytes32(record_hash)
            status_int = self.chain.contract.functions.getRecordStatus(b32_record).call()
            return STATUS_MAP.get(int(status_int), f"STATUS_{status_int}")
        except Exception:
            return "UNKNOWN"

    def get_dispute_record(self, record_hash: str) -> dict[str, Any] | None:
        if not self.chain.contract:
            return None
        try:
            b32_record = self._format_bytes32(record_hash)
            disp = self.chain.contract.functions.getDispute(b32_record).call()
            return {
                "claimant": disp[0],
                "reason_code": int(disp[1]),
                "evidence_cid": disp[2],
                "timestamp": int(disp[3]),
                "resolved": bool(disp[4]),
            }
        except Exception:
            return None

    def get_nonce(self, address: str) -> int:
        if not self.chain.contract:
            return 0
        try:
            chk = Web3.to_checksum_address(address)
            return int(self.chain.contract.functions.getNonce(chk).call())
        except Exception:
            return 0

    def submit_takedown(
        self,
        record_hash: str,
        reason_code: int,
        evidence_ipfs_cid: str,
        deadline: int | None = None,
        private_key: str | None = None,
    ) -> dict[str, Any]:
        pk = private_key or self.private_key
        if not pk:
            raise RuntimeError("Private key is required to sign takedown claim.")
        if not self.chain.contract:
            raise RuntimeError("Contract is not deployed.")

        signer_account = Account.from_key(pk)
        claimant = signer_account.address
        if deadline is None:
            deadline = int(time.time()) + 86400

        nonce = self.get_nonce(claimant)
        chain_id = self.chain.w3.eth.chain_id
        contract_addr = self.chain.contract_address

        sig_hex, _claimant_rec, _ = sign_takedown_claim(
            private_key=pk,
            record_hash=record_hash,
            reason_code=reason_code,
            evidence_ipfs_cid=evidence_ipfs_cid,
            nonce=nonce,
            deadline=deadline,
            chain_id=chain_id,
            contract_address=contract_addr,
        )

        b32_record = self._format_bytes32(record_hash)
        sig_bytes = bytes.fromhex(sig_hex.removeprefix("0x"))

        account_nonce = self.chain.w3.eth.get_transaction_count(self.account.address, "pending")
        txn = self.chain.contract.functions.submitTakedownClaim(
            b32_record,
            Web3.to_checksum_address(claimant),
            reason_code,
            evidence_ipfs_cid,
            deadline,
            sig_bytes,
        ).build_transaction({
            "from": self.account.address,
            "nonce": account_nonce,
            "chainId": chain_id,
            "gas": 300000,
            "maxFeePerGas": self.chain.w3.to_wei("30", "gwei"),
            "maxPriorityFeePerGas": self.chain.w3.to_wei("1.5", "gwei"),
        })

        signed_txn = self.chain.w3.eth.account.sign_transaction(txn, private_key=self.private_key)
        tx_hash_bytes = self.chain.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_hash = "0x" + tx_hash_bytes.hex()
        receipt = self.chain.w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=60)

        return {
            "status": "success" if receipt.status == 1 else "failed",
            "tx_hash": tx_hash,
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "record_hash": record_hash,
            "claimant": claimant,
            "reason_code": reason_code,
            "evidence_cid": evidence_ipfs_cid,
            "new_record_status": "DISPUTED",
        }

    def resolve_dispute(
        self,
        record_hash: str,
        new_status: int | str,
    ) -> dict[str, Any]:
        if not self.chain.contract:
            raise RuntimeError("Contract is not deployed.")

        if isinstance(new_status, str):
            status_int = STATUS_TO_INT.get(new_status.upper(), 0)
        else:
            status_int = int(new_status)

        b32_record = self._format_bytes32(record_hash)
        chain_id = self.chain.w3.eth.chain_id
        account_nonce = self.chain.w3.eth.get_transaction_count(self.account.address, "pending")

        txn = self.chain.contract.functions.resolveDispute(
            b32_record,
            status_int,
        ).build_transaction({
            "from": self.account.address,
            "nonce": account_nonce,
            "chainId": chain_id,
            "gas": 200000,
            "maxFeePerGas": self.chain.w3.to_wei("30", "gwei"),
            "maxPriorityFeePerGas": self.chain.w3.to_wei("1.5", "gwei"),
        })

        signed_txn = self.chain.w3.eth.account.sign_transaction(txn, private_key=self.private_key)
        tx_hash_bytes = self.chain.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_hash = "0x" + tx_hash_bytes.hex()
        receipt = self.chain.w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=60)

        return {
            "status": "success" if receipt.status == 1 else "failed",
            "tx_hash": tx_hash,
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "record_hash": record_hash,
            "resolved_status": STATUS_MAP.get(status_int, f"STATUS_{status_int}"),
        }
