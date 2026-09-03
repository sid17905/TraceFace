const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("FaceProvenanceRegistry Smart Contract", function () {
  let registry;
  let owner;
  let addr1;
  let addr2;

  const sampleRecordHash = ethers.keccak256(ethers.toUtf8Bytes("canonical_provenance_payload_1"));
  const sampleIpfsCid = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi";
  const sampleFaceVectorHash = ethers.keccak256(ethers.toUtf8Bytes("arcface_512d_vector_embedding"));
  const evidenceCid = "bafybeic96cdf18205ddf30d4df5c075ebde9b01fb04c5f39065a";

  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();
    const FaceProvenanceRegistry = await ethers.getContractFactory("FaceProvenanceRegistry");
    registry = await FaceProvenanceRegistry.deploy();
    await registry.waitForDeployment();
  });

  describe("Registration", function () {
    it("should register a new provenance record successfully", async function () {
      const tx = await registry.registerProvenance(sampleRecordHash, sampleIpfsCid, sampleFaceVectorHash);
      await tx.wait();

      expect(await registry.getRecordCount()).to.equal(1);

      const [exists, ipfsCid, faceVectorHash, timestamp, registrant] = await registry.verifyProvenance(sampleRecordHash);
      expect(exists).to.be.true;
      expect(ipfsCid).to.equal(sampleIpfsCid);
      expect(faceVectorHash).to.equal(sampleFaceVectorHash);
      expect(registrant).to.equal(owner.address);
      expect(timestamp).to.be.greaterThan(0);
      expect(await registry.getRecordStatus(sampleRecordHash)).to.equal(0);
    });

    it("should emit ProvenanceRegistered event with correct arguments", async function () {
      await expect(registry.registerProvenance(sampleRecordHash, sampleIpfsCid, sampleFaceVectorHash))
        .to.emit(registry, "ProvenanceRegistered")
        .withArgs(sampleRecordHash, sampleIpfsCid, sampleFaceVectorHash, owner.address, (val) => val > 0);
    });

    it("should revert if record is registered twice (duplicate protection)", async function () {
      await registry.registerProvenance(sampleRecordHash, sampleIpfsCid, sampleFaceVectorHash);
      await expect(
        registry.registerProvenance(sampleRecordHash, sampleIpfsCid, sampleFaceVectorHash)
      ).to.be.revertedWithCustomError(registry, "RecordAlreadyExists");
    });

    it("should revert on empty recordHash", async function () {
      await expect(
        registry.registerProvenance(ethers.ZeroHash, sampleIpfsCid, sampleFaceVectorHash)
      ).to.be.revertedWithCustomError(registry, "InvalidRecordHash");
    });

    it("should revert on empty IPFS CID", async function () {
      await expect(
        registry.registerProvenance(sampleRecordHash, "", sampleFaceVectorHash)
      ).to.be.revertedWithCustomError(registry, "InvalidIpfsCid");
    });

    it("should revert on empty faceVectorHash", async function () {
      await expect(
        registry.registerProvenance(sampleRecordHash, sampleIpfsCid, ethers.ZeroHash)
      ).to.be.revertedWithCustomError(registry, "InvalidFaceVectorHash");
    });
  });

  describe("Verification & Lookups", function () {
    it("should return false for non-existent record", async function () {
      const nonExistentHash = ethers.keccak256(ethers.toUtf8Bytes("random_non_existent"));
      const [exists, ipfsCid, faceVectorHash, timestamp, registrant] = await registry.verifyProvenance(nonExistentHash);
      expect(exists).to.be.false;
      expect(ipfsCid).to.equal("");
      expect(faceVectorHash).to.equal(ethers.ZeroHash);
      expect(timestamp).to.equal(0);
      expect(registrant).to.equal(ethers.ZeroAddress);
    });

    it("should allow finding record hash by face vector hash", async function () {
      await registry.registerProvenance(sampleRecordHash, sampleIpfsCid, sampleFaceVectorHash);
      const linkedRecordHash = await registry.getRecordByVector(sampleFaceVectorHash);
      expect(linkedRecordHash).to.equal(sampleRecordHash);
    });
  });

  describe("EIP-712 Takedown Claims & Dispute Resolution", function () {
    beforeEach(async function () {
      await registry.registerProvenance(sampleRecordHash, sampleIpfsCid, sampleFaceVectorHash);
    });

    it("should process valid EIP-712 takedown claim", async function () {
      const { chainId } = await ethers.provider.getNetwork();
      const contractAddress = await registry.getAddress();
      const nonce = await registry.getNonce(addr1.address);
      const deadline = Math.floor(Date.now() / 1000) + 3600;
      const reasonCode = 1;

      const domain = {
        name: "TraceFace Provenance Registry",
        version: "1",
        chainId: chainId,
        verifyingContract: contractAddress,
      };

      const types = {
        TakedownClaim: [
          { name: "recordHash", type: "bytes32" },
          { name: "claimant", type: "address" },
          { name: "reasonCode", type: "uint8" },
          { name: "evidenceIpfsCid", type: "string" },
          { name: "nonce", type: "uint256" },
          { name: "deadline", type: "uint256" },
        ],
      };

      const value = {
        recordHash: sampleRecordHash,
        claimant: addr1.address,
        reasonCode: reasonCode,
        evidenceIpfsCid: evidenceCid,
        nonce: nonce,
        deadline: deadline,
      };

      const signature = await addr1.signTypedData(domain, types, value);

      await expect(
        registry.submitTakedownClaim(
          sampleRecordHash,
          addr1.address,
          reasonCode,
          evidenceCid,
          deadline,
          signature
        )
      ).to.emit(registry, "TakedownClaimSubmitted")
        .withArgs(sampleRecordHash, addr1.address, reasonCode, evidenceCid, (val) => val > 0);

      expect(await registry.getRecordStatus(sampleRecordHash)).to.equal(1);
      const dispute = await registry.getDispute(sampleRecordHash);
      expect(dispute.claimant).to.equal(addr1.address);
      expect(dispute.reasonCode).to.equal(reasonCode);
      expect(dispute.evidenceCid).to.equal(evidenceCid);
      expect(dispute.resolved).to.be.false;
    });

    it("should allow direct takedown claim submission", async function () {
      await registry.connect(addr1).submitTakedownClaimDirect(sampleRecordHash, 2, evidenceCid);
      expect(await registry.getRecordStatus(sampleRecordHash)).to.equal(1);
    });

    it("should resolve dispute to REVOKED", async function () {
      await registry.connect(addr1).submitTakedownClaimDirect(sampleRecordHash, 1, evidenceCid);
      await registry.resolveDispute(sampleRecordHash, 2);

      expect(await registry.getRecordStatus(sampleRecordHash)).to.equal(2);
      const [exists] = await registry.verifyProvenance(sampleRecordHash);
      expect(exists).to.be.false;
    });

    it("should resolve dispute to CONFIRMED", async function () {
      await registry.connect(addr1).submitTakedownClaimDirect(sampleRecordHash, 1, evidenceCid);
      await registry.resolveDispute(sampleRecordHash, 3);

      expect(await registry.getRecordStatus(sampleRecordHash)).to.equal(3);
      const [exists] = await registry.verifyProvenance(sampleRecordHash);
      expect(exists).to.be.true;
    });

    it("should reject dispute resolution from unauthorized accounts", async function () {
      await registry.connect(addr1).submitTakedownClaimDirect(sampleRecordHash, 1, evidenceCid);
      await expect(
        registry.connect(addr2).resolveDispute(sampleRecordHash, 2)
      ).to.be.revertedWithCustomError(registry, "Unauthorized");
    });
  });
});
