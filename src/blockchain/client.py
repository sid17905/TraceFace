import json
import os
from pathlib import Path
from typing import Any

from eth_account import Account
from web3 import Web3


class BlockchainClient:
    def __init__(
        self,
        rpc_url: str | None = None,
        contract_address: str | None = None,
        private_key: str | None = None,
        abi_path: str | None = None,
    ):
        self.rpc_url = rpc_url or os.getenv("RPC_URL", "http://127.0.0.1:8545")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        self.private_key = (
            private_key
            or os.getenv("PRIVATE_KEY")
            or "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        )
        self.account = Account.from_key(self.private_key)

        abi, detected_address = self._load_contract_metadata(abi_path)
        self.contract_address = contract_address or os.getenv("CONTRACT_ADDRESS") or detected_address
        
        if self.contract_address and self.contract_address != "0x0000000000000000000000000000000000000000":
            self.contract_address = Web3.to_checksum_address(self.contract_address)
            self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi)  # type: ignore
        else:
            self.contract = None  # type: ignore

    def _load_contract_metadata(self, custom_path: str | None) -> tuple[list, str]:
        path = (
            Path(custom_path)
            if custom_path
            else Path(__file__).parent / "contract_abi.json"
        )
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("abi", []), data.get("address", "")
        return [], ""

    def is_connected(self) -> bool:
        try:
            return self.w3.is_connected()
        except Exception:  # noqa: BLE001
            return False

    def _format_bytes32(self, hex_val: str) -> bytes:
        clean = hex_val.removeprefix("0x")
        clean = clean.zfill(64)[:64]
        return bytes.fromhex(clean)

    def register_provenance(
        self,
        record_hash: str,
        ipfs_cid: str,
        face_vector_hash: str,
    ) -> dict[str, Any]:
        """
        Signs and broadcasts registerProvenance transaction to EVM blockchain.
        """
        if not self.contract:
            raise RuntimeError("Contract is not deployed or address not configured.")

        b32_record = self._format_bytes32(record_hash)
        b32_vector = self._format_bytes32(face_vector_hash)

        # Check if already exists
        exists, _, _, _, _ = self.contract.functions.verifyProvenance(b32_record).call()
        if exists:
            return {
                "status": "already_registered",
                "record_hash": record_hash,
                "ipfs_cid": ipfs_cid,
                "tx_hash": None,
                "message": "Record hash already anchored on-chain.",
            }

        nonce = self.w3.eth.get_transaction_count(self.account.address, "pending")
        chain_id = self.w3.eth.chain_id

        txn = self.contract.functions.registerProvenance(
            b32_record,
            ipfs_cid,
            b32_vector
        ).build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "chainId": chain_id,
            "gas": 250000,
            "maxFeePerGas": self.w3.to_wei("30", "gwei"),
            "maxPriorityFeePerGas": self.w3.to_wei("1.5", "gwei"),
        })

        signed_txn = self.w3.eth.account.sign_transaction(txn, private_key=self.private_key)
        tx_hash_bytes = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_hash = "0x" + tx_hash_bytes.hex()

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=60)

        return {
            "status": "success" if receipt.status == 1 else "failed",  # type: ignore
            "tx_hash": tx_hash,
            "block_number": receipt.blockNumber,  # type: ignore
            "gas_used": receipt.gasUsed,  # type: ignore
            "record_hash": record_hash,
            "ipfs_cid": ipfs_cid,
            "face_vector_hash": face_vector_hash,
            "registrant": self.account.address,
        }

    def get_provenance(self, record_hash: str) -> dict[str, Any]:
        if not self.contract:
            raise RuntimeError("Contract is not configured.")

        b32_record = self._format_bytes32(record_hash)
        exists, ipfs_cid, face_vector_hash, timestamp, registrant = (
            self.contract.functions.verifyProvenance(b32_record).call()
        )

        return {
            "exists": exists,
            "record_hash": record_hash,
            "ipfs_cid": ipfs_cid,
            "face_vector_hash": "0x" + face_vector_hash.hex() if isinstance(face_vector_hash, bytes) else str(face_vector_hash),
            "timestamp": timestamp,
            "registrant": registrant,
        }

    def get_record_by_vector(self, face_vector_hash: str) -> str:
        if not self.contract:
            raise RuntimeError("Contract is not configured.")

        b32_vector = self._format_bytes32(face_vector_hash)
        res_bytes = self.contract.functions.getRecordByVector(b32_vector).call()
        return "0x" + res_bytes.hex() if isinstance(res_bytes, bytes) else str(res_bytes)
