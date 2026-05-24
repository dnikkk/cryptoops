// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console2} from "forge-std/Script.sol";
import {TestToken} from "../contracts/TestToken.sol";
import {MerkleClaim} from "../contracts/MerkleClaim.sol";

/// @notice campaigns/eftemonia-safe-sepolia-004 — Eftemonia → Safe 0x03E4…dEff
/// forge script script/DeployEftemoniaSafe.s.sol:DeployEftemoniaSafe --rpc-url sepolia --broadcast -vvvv
contract DeployEftemoniaSafe is Script {
    bytes32 constant MERKLE_ROOT = 0xb5f8c9f65c650eeabd8c84f0873a51ad4986b1a1f165ef997ed910055639848d;

    uint256 constant FUND_CLAIM_CONTRACT = 180 * 1e8;

    string constant TOKEN_NAME = "Eftemonia";
    string constant TOKEN_SYMBOL = "EFTEMONIA";
    uint8 constant TOKEN_DECIMALS = 8;

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);

        vm.startBroadcast(deployerPrivateKey);

        TestToken token = new TestToken(deployer, TOKEN_NAME, TOKEN_SYMBOL, TOKEN_DECIMALS);
        MerkleClaim claim = new MerkleClaim(deployer, token, MERKLE_ROOT);

        token.mint(address(claim), FUND_CLAIM_CONTRACT);

        vm.stopBroadcast();

        console2.log("Campaign: eftemonia-safe-sepolia-004");
        console2.log("Deployer:", deployer);
        console2.log("Whitelist Safe:", 0x03E400726D7744f255a160c51De83A035435dEff);
        console2.log("Token:", address(token));
        console2.log("MerkleClaim:", address(claim));
        console2.log("Merkle root:", uint256(MERKLE_ROOT));
    }
}
