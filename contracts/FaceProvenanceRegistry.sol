// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./interfaces/IFaceProvenanceRegistry.sol";

/**
 * @title FaceProvenanceRegistry
 * @dev Gas-optimized decentralized registry for biometric OSINT provenance records with EIP-712 takedown disputes.
 */
contract FaceProvenanceRegistry is IFaceProvenanceRegistry, EIP712, Ownable {
    using ECDSA for bytes32;

    bytes32 private constant _TAKEDOWN_CLAIM_TYPEHASH = keccak256(
        "TakedownClaim(bytes32 recordHash,address claimant,uint8 reasonCode,string evidenceIpfsCid,uint256 nonce,uint256 deadline)"
    );

    mapping(bytes32 => ProvenanceRecord) private _records;
    mapping(bytes32 => bytes32) private _vectorToRecord;
    mapping(bytes32 => DisputeRecord) private _disputes;
    mapping(address => uint256) private _nonces;
    uint256 private _recordCount;

    constructor()
        EIP712("TraceFace Provenance Registry", "1")
        Ownable(msg.sender)
    {}

    function registerProvenance(
        bytes32 recordHash,
        string calldata ipfsCid,
        bytes32 faceVectorHash
    ) external override returns (bool) {
        if (recordHash == bytes32(0)) revert InvalidRecordHash();
        if (bytes(ipfsCid).length == 0) revert InvalidIpfsCid();
        if (faceVectorHash == bytes32(0)) revert InvalidFaceVectorHash();
        if (_records[recordHash].isValid) revert RecordAlreadyExists(recordHash);

        _records[recordHash] = ProvenanceRecord({
            recordHash: recordHash,
            ipfsCid: ipfsCid,
            faceVectorHash: faceVectorHash,
            timestamp: uint64(block.timestamp),
            registrant: msg.sender,
            isValid: true,
            status: RecordStatus.ACTIVE
        });

        _vectorToRecord[faceVectorHash] = recordHash;
        _recordCount += 1;

        emit ProvenanceRegistered(
            recordHash,
            ipfsCid,
            faceVectorHash,
            msg.sender,
            uint64(block.timestamp)
        );

        return true;
    }

    function verifyProvenance(
        bytes32 recordHash
    ) external view override returns (
        bool exists,
        string memory ipfsCid,
        bytes32 faceVectorHash,
        uint64 timestamp,
        address registrant
    ) {
        ProvenanceRecord storage record = _records[recordHash];
        if (!record.isValid && record.status != RecordStatus.REVOKED && record.status != RecordStatus.DISPUTED) {
            return (false, "", bytes32(0), 0, address(0));
        }
        return (
            record.isValid,
            record.ipfsCid,
            record.faceVectorHash,
            record.timestamp,
            record.registrant
        );
    }

    function getRecordByVector(
        bytes32 faceVectorHash
    ) external view override returns (bytes32 recordHash) {
        return _vectorToRecord[faceVectorHash];
    }

    function getRecordCount() external view override returns (uint256) {
        return _recordCount;
    }

    function submitTakedownClaim(
        bytes32 recordHash,
        address claimant,
        uint8 reasonCode,
        string calldata evidenceIpfsCid,
        uint256 deadline,
        bytes calldata signature
    ) external override returns (bool) {
        if (block.timestamp > deadline) revert InvalidDeadline();
        if (claimant == address(0)) revert InvalidSignature();

        ProvenanceRecord storage record = _records[recordHash];
        if (record.recordHash == bytes32(0)) revert RecordNotFound(recordHash);

        uint256 currentNonce = _nonces[claimant]++;
        bytes32 structHash = keccak256(
            abi.encode(
                _TAKEDOWN_CLAIM_TYPEHASH,
                recordHash,
                claimant,
                reasonCode,
                keccak256(bytes(evidenceIpfsCid)),
                currentNonce,
                deadline
            )
        );

        bytes32 digest = _hashTypedDataV4(structHash);
        address recovered = digest.recover(signature);
        if (recovered != claimant) revert InvalidSignature();

        _disputes[recordHash] = DisputeRecord({
            claimant: claimant,
            reasonCode: reasonCode,
            evidenceCid: evidenceIpfsCid,
            timestamp: block.timestamp,
            resolved: false
        });

        record.status = RecordStatus.DISPUTED;

        emit TakedownClaimSubmitted(
            recordHash,
            claimant,
            reasonCode,
            evidenceIpfsCid,
            block.timestamp
        );

        return true;
    }

    function submitTakedownClaimDirect(
        bytes32 recordHash,
        uint8 reasonCode,
        string calldata evidenceIpfsCid
    ) external override returns (bool) {
        ProvenanceRecord storage record = _records[recordHash];
        if (record.recordHash == bytes32(0)) revert RecordNotFound(recordHash);

        _disputes[recordHash] = DisputeRecord({
            claimant: msg.sender,
            reasonCode: reasonCode,
            evidenceCid: evidenceIpfsCid,
            timestamp: block.timestamp,
            resolved: false
        });

        record.status = RecordStatus.DISPUTED;

        emit TakedownClaimSubmitted(
            recordHash,
            msg.sender,
            reasonCode,
            evidenceIpfsCid,
            block.timestamp
        );

        return true;
    }

    function resolveDispute(
        bytes32 recordHash,
        RecordStatus newStatus
    ) external override returns (bool) {
        ProvenanceRecord storage record = _records[recordHash];
        if (record.recordHash == bytes32(0)) revert RecordNotFound(recordHash);

        if (msg.sender != owner() && msg.sender != record.registrant && msg.sender != _disputes[recordHash].claimant) {
            revert Unauthorized();
        }

        record.status = newStatus;
        if (newStatus == RecordStatus.REVOKED) {
            record.isValid = false;
        } else if (newStatus == RecordStatus.ACTIVE || newStatus == RecordStatus.CONFIRMED) {
            record.isValid = true;
        }

        _disputes[recordHash].resolved = true;

        emit DisputeResolved(recordHash, newStatus, msg.sender, block.timestamp);
        return true;
    }

    function getRecordStatus(
        bytes32 recordHash
    ) external view override returns (RecordStatus) {
        ProvenanceRecord storage record = _records[recordHash];
        if (record.recordHash == bytes32(0)) revert RecordNotFound(recordHash);
        return record.status;
    }

    function getDispute(
        bytes32 recordHash
    ) external view override returns (DisputeRecord memory) {
        return _disputes[recordHash];
    }

    function getNonce(
        address claimant
    ) external view override returns (uint256) {
        return _nonces[claimant];
    }
}
