// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {TestToken} from "../contracts/TestToken.sol";
import {MerkleClaim} from "../contracts/MerkleClaim.sol";

contract MerkleClaimTest is Test {
    bytes32 constant ROOT = 0xfde04f44bdb5e29ce3a74c3be1543223794d94e61805805e00d432d4030015b2;

    TestToken token;
    MerkleClaim claim;

    function setUp() public {
        token = new TestToken(address(this), "Eftihia", "EFTIHIA", 6);
        claim = new MerkleClaim(address(this), token, ROOT);
        token.mint(address(claim), 5_400_000 * 1e6);
    }

    function test_claim_first_wallet() public {
        address user = 0x6886654B5745EAbB1517eF9D8556c5b3dc86646f;
        uint256 amount = 1_800_000 * 1e6;
        bytes32[] memory proof = new bytes32[](2);
        proof[0] = 0x1abc206e4eacdb63933560c720fe64fcfe166ed1ac7f0e99949082b4779c7237;
        proof[1] = 0xcfadfbdc1f61ba0a60ce955b9c7dea2f9bce3bdcd0a5ebd66644ed088cd326b0;

        vm.prank(user);
        claim.claim(amount, proof);

        assertEq(token.balanceOf(user), amount);
        assertTrue(claim.hasClaimed(user));
    }
}
