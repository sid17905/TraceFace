// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./interfaces/IFaceProvenanceRegistry.sol";

/**
 * @title FaceProvenanceRegistry
 * @dev Gas-optimized decentralized registry for biometric OSINT provenance records.
 */
contract FaceProvenanceRegistry is IFaceProvenanceRegistry {
    mapping(bytes32 => ProvenanceRecord) private _records;
    mapping(bytes32 => bytes32) private _vectorToRecord;
    uint256 private _recordCount;

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
            isValid: true
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
        if (!record.isValid) {
            return (false, "", bytes32(0), 0, address(0));
        }
        return (
            true,
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
}
