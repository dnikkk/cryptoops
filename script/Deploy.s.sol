// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console2} from "forge-std/Script.sol";
import {TestToken} from "../contracts/TestToken.sol";
import {MerkleClaim} from "../contracts/MerkleClaim.sol";

/// @notice Deploy TestToken + MerkleClaim on Sepolia.
/// @dev Universal FLOW, campaign-specific CONSTANTS — see script/README.md
///      Before each new campaign: update MERKLE_ROOT + FUND_CLAIM_CONTRACT from
///      campaigns/<id>/output/proof.json and whitelist totals.
/// forge script script/Deploy.s.sol:Deploy --rpc-url sepolia --broadcast -vvvv
contract Deploy is Script {
    // campaigns/eftemonia-sepolia-002 — change for each new campaign
    bytes32 constant MERKLE_ROOT = 0xfa7336e60b0e9376ec62a579beaec2171cb29f4e716a275a13e4649286a30bc6;

    // Sum of whitelist raw amounts: 3 × 60 × 1e8
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

        console2.log("Deployer:", deployer);
        console2.log("Token (TestToken):", address(token));
        console2.log("MerkleClaim:", address(claim));
        console2.log("Merkle root:", uint256(MERKLE_ROOT));
        console2.log("Claim contract balance:", token.balanceOf(address(claim)));
    }
}
