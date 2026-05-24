// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console2} from "forge-std/Script.sol";
import {TestToken} from "../contracts/TestToken.sol";
import {MerkleClaim} from "../contracts/MerkleClaim.sol";

/// @notice campaigns/eftihia-safe-sepolia-003 — Eftihia → Safe 0x435A…a8d1
/// forge script script/DeployEftihiaSafe.s.sol:DeployEftihiaSafe --rpc-url sepolia --broadcast -vvvv
contract DeployEftihiaSafe is Script {
    bytes32 constant MERKLE_ROOT = 0x1520ae2b53f0f0581064f98e481f524369efddfadaf7a7fd6310f943a2391408;

    uint256 constant FUND_CLAIM_CONTRACT = 5_400_000 * 1e6;

    string constant TOKEN_NAME = "Eftihia";
    string constant TOKEN_SYMBOL = "EFTIHIA";
    uint8 constant TOKEN_DECIMALS = 6;

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);

        vm.startBroadcast(deployerPrivateKey);

        TestToken token = new TestToken(deployer, TOKEN_NAME, TOKEN_SYMBOL, TOKEN_DECIMALS);
        MerkleClaim claim = new MerkleClaim(deployer, token, MERKLE_ROOT);

        token.mint(address(claim), FUND_CLAIM_CONTRACT);

        vm.stopBroadcast();

        console2.log("Campaign: eftihia-safe-sepolia-003");
        console2.log("Deployer:", deployer);
        console2.log("Whitelist Safe:", 0x435A0e13cA88b467C3371E78418fAeaB5721a8d1);
        console2.log("Token:", address(token));
        console2.log("MerkleClaim:", address(claim));
        console2.log("Merkle root:", uint256(MERKLE_ROOT));
    }
}
