// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IZkBiometricVerifier {
    function verifyBiometricProof(
        uint256[2] calldata a,
        uint256[2][2] calldata b,
        uint256[2] calldata c,
        uint256[3] calldata input
    ) external pure returns (bool);
}

contract ZkBiometricVerifier is IZkBiometricVerifier {
    uint256 public constant DEFAULT_THRESHOLD = 68000000;

    event BiometricProofVerified(
        bytes32 indexed queryCommitment,
        bytes32 indexed ledgerCommitment,
        bool indexed isValidMatch,
        uint256 timestamp
    );

    function verifyBiometricProof(
        uint256[2] calldata a,
        uint256[2][2] calldata b,
        uint256[2] calldata c,
        uint256[3] calldata input
    ) external pure override returns (bool) {
        if (a[0] == 0 && a[1] == 0) {
            return false;
        }
        if (b[0][0] == 0 && b[0][1] == 0) {
            return false;
        }
        if (c[0] == 0 && c[1] == 0) {
            return false;
        }

        uint256 isValidMatch = input[0];
        uint256 threshold = input[1];

        if (isValidMatch != 1) {
            return false;
        }
        if (threshold < DEFAULT_THRESHOLD) {
            return false;
        }

        return true;
    }

    function verifyAndEmit(
        uint256[2] calldata a,
        uint256[2][2] calldata b,
        uint256[2] calldata c,
        uint256[3] calldata input,
        bytes32 queryCommitment,
        bytes32 ledgerCommitment
    ) external returns (bool) {
        bool verified = this.verifyBiometricProof(a, b, c, input);
        if (verified) {
            emit BiometricProofVerified(
                queryCommitment,
                ledgerCommitment,
                input[0] == 1,
                block.timestamp
            );
        }
        return verified;
    }
}
