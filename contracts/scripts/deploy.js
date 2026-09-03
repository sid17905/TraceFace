const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log(`[+] Deploying FaceProvenanceRegistry with account: ${deployer.address}`);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log(`[+] Account balance: ${ethers.formatEther(balance)} ETH`);

  const FaceProvenanceRegistry = await ethers.getContractFactory("FaceProvenanceRegistry");
  const registry = await FaceProvenanceRegistry.deploy();
  await registry.waitForDeployment();

  const contractAddress = await registry.getAddress();
  console.log(`[✔] FaceProvenanceRegistry deployed successfully at: ${contractAddress}`);

  const artifactPath = path.join(__dirname, "../../artifacts/contracts/FaceProvenanceRegistry.sol/FaceProvenanceRegistry.json");
  let abi = [];
  if (fs.existsSync(artifactPath)) {
    const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
    abi = artifact.abi;
  }

  const outputPayload = {
    address: contractAddress,
    network: (await ethers.provider.getNetwork()).name,
    chainId: Number((await ethers.provider.getNetwork()).chainId),
    deployedAt: new Date().toISOString(),
    deployer: deployer.address,
    abi: abi,
  };

  const blockchainDir = path.join(__dirname, "../../src/blockchain");
  if (!fs.existsSync(blockchainDir)) {
    fs.mkdirSync(blockchainDir, { recursive: true });
  }

  const exportPath = path.join(blockchainDir, "contract_abi.json");
  fs.writeFileSync(exportPath, JSON.stringify(outputPayload, null, 2));
  console.log(`[✔] Exported ABI and deployment metadata to: ${exportPath}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("[-] Deployment failed:", error);
    process.exit(1);
  });
