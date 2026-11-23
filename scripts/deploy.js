
const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    const accounts = await ethers.getSigners();

    const kreator = accounts[0];
    const produser = accounts[1];
    const penulisLagu = accounts[2];
    const platformMusik = accounts[3];

    const MusicRoyalty = await ethers.getContractFactory("MusicRoyalty");

    const musicRoyalty = await MusicRoyalty.deploy(
        kreator.address,
        produser.address,
        penulisLagu.address,
        platformMusik.address
    );

    await musicRoyalty.waitForDeployment();

    const contractAddress = await musicRoyalty.getAddress();
    const network = await ethers.provider.getNetwork();

    const deploymentData = {
        contractAddress: contractAddress,
        network: network.name,
        chainId: Number(network.chainId),
        deployedAt: new Date().toISOString()
    };

    const filePath = path.join(__dirname, "..", "deployment.json");

    fs.writeFileSync(
        filePath,
        JSON.stringify(deploymentData, null, 4)
    );

    console.log("MusicRoyalty berhasil di-deploy!");
    console.log("Contract Address:", contractAddress);
    console.log("Deployment tersimpan di deployment.json");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
