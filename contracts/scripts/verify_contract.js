const { run } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const metadataPath = path.join(__dirname, "../../src/blockchain/contract_abi.json");
  if (!fs.existsSync(metadataPath)) {
    throw new Error("Deployment metadata not found at src/blockchain/contract_abi.json");
  }

  const metadata = JSON.parse(fs.readFileSync(metadataPath, "utf8"));
  console.log(`[+] Verifying contract at: ${metadata.address} on network ${metadata.network}`);

  try {
    await run("verify:verify", {
      address: metadata.address,
      constructorArguments: [],
    });
    console.log("[✔] Contract verified successfully on block explorer!");
  } catch (error) {
    console.error("[-] Verification failed:", error.message);
  }
}

main()
  .then(() => process.exit(0))
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
