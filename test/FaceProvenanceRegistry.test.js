const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("FaceProvenanceRegistry Smart Contract", function () {
  let registry;
  let owner;
  let addr1;

  const sampleRecordHash = ethers.keccak256(ethers.toUtf8Bytes("canonical_provenance_payload_1"));
  const sampleIpfsCid = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi";
  const sampleFaceVectorHash = ethers.keccak256(ethers.toUtf8Bytes("arcface_512d_vector_embedding"));

  beforeEach(async function () {
    [owner, addr1] = await ethers.getSigners();
    const FaceProvenanceRegistry = await ethers.getContractFactory("FaceProvenanceRegistry");
    registry = await FaceProvenanceRegistry.deploy();
    await registry.waitForDeployment();
  });

  describe("Registration", function () {
    it("should register a new provenance record successfully", async function () {
      const tx = await registry.registerProvenance(sampleRecordHash, sampleIpfsCid, sampleFaceVectorHash);
      const receipt = await tx.wait();

      expect(await registry.getRecordCount()).to.equal(1);

      const [exists, ipfsCid, faceVectorHash, timestamp, registrant] = await registry.verifyProvenance(sampleRecordHash);
      expect(exists).to.be.true;
      expect(ipfsCid).to.equal(sampleIpfsCid);
      expect(faceVectorHash).to.equal(sampleFaceVectorHash);
      expect(registrant).to.equal(owner.address);
      expect(timestamp).to.be.greaterThan(0);
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
});
