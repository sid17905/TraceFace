// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IFaceProvenanceRegistry {
    enum RecordStatus {
        ACTIVE,
        DISPUTED,
        REVOKED,
        CONFIRMED
    }

    struct DisputeRecord {
        address claimant;
        uint8 reasonCode;
        string evidenceCid;
        uint256 timestamp;
        bool resolved;
    }

    struct ProvenanceRecord {
        bytes32 recordHash;
        string ipfsCid;
        bytes32 faceVectorHash;
        uint64 timestamp;
        address registrant;
        bool isValid;
        RecordStatus status;
    }

    event ProvenanceRegistered(
        bytes32 indexed recordHash,
        string ipfsCid,
        bytes32 indexed faceVectorHash,
        address indexed registrant,
        uint64 timestamp
    );

    event TakedownClaimSubmitted(
        bytes32 indexed recordHash,
        address indexed claimant,
        uint8 reasonCode,
        string evidenceCid,
        uint256 timestamp
    );

    event DisputeResolved(
        bytes32 indexed recordHash,
        RecordStatus newStatus,
        address indexed resolver,
        uint256 timestamp
    );

    error RecordAlreadyExists(bytes32 recordHash);
    error RecordNotFound(bytes32 recordHash);
    error InvalidRecordHash();
    error InvalidIpfsCid();
    error InvalidFaceVectorHash();
    error InvalidSignature();
    error InvalidDeadline();
    error InvalidNonce();
    error Unauthorized();

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

    function submitTakedownClaim(
        bytes32 recordHash,
        address claimant,
        uint8 reasonCode,
        string calldata evidenceIpfsCid,
        uint256 deadline,
        bytes calldata signature
    ) external returns (bool);

    function submitTakedownClaimDirect(
        bytes32 recordHash,
        uint8 reasonCode,
        string calldata evidenceIpfsCid
    ) external returns (bool);

    function resolveDispute(
        bytes32 recordHash,
        RecordStatus newStatus
    ) external returns (bool);

    function getRecordStatus(
        bytes32 recordHash
    ) external view returns (RecordStatus);

    function getDispute(
        bytes32 recordHash
    ) external view returns (DisputeRecord memory);

    function getNonce(
        address claimant
    ) external view returns (uint256);
}
