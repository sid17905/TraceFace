// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IFaceProvenanceRegistry {
    struct ProvenanceRecord {
        bytes32 recordHash;
        string ipfsCid;
        bytes32 faceVectorHash;
        uint64 timestamp;
        address registrant;
        bool isValid;
    }

    event ProvenanceRegistered(
        bytes32 indexed recordHash,
        string ipfsCid,
        bytes32 indexed faceVectorHash,
        address indexed registrant,
        uint64 timestamp
    );

    error RecordAlreadyExists(bytes32 recordHash);
    error InvalidRecordHash();
    error InvalidIpfsCid();
    error InvalidFaceVectorHash();

    function registerProvenance(
        bytes32 recordHash,
        string calldata ipfsCid,
        bytes32 faceVectorHash
    ) external returns (bool);

    function verifyProvenance(
        bytes32 recordHash
    ) external view returns (
        bool exists,
        string memory ipfsCid,
        bytes32 faceVectorHash,
        uint64 timestamp,
        address registrant
    );

    function getRecordByVector(
        bytes32 faceVectorHash
    ) external view returns (bytes32 recordHash);

    function getRecordCount() external view returns (uint256);
}
