// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {MerkleProof} from "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/// @notice Merkle airdrop claim — leaf encoding matches @openzeppelin/merkle-tree StandardMerkleTree:
/// keccak256(bytes.concat(keccak256(abi.encode(address, uint256))))
contract MerkleClaim is Ownable {
    IERC20 public immutable token;
    bytes32 public immutable merkleRoot;

    mapping(address => bool) public hasClaimed;

    event Claimed(address indexed account, uint256 amount);

    constructor(
        address initialOwner,
        IERC20 token_,
        bytes32 merkleRoot_
    ) Ownable(initialOwner) {
        token = token_;
        merkleRoot = merkleRoot_;
    }

    function claim(uint256 amount, bytes32[] calldata proof) external {
        require(!hasClaimed[msg.sender], "Already claimed");

        bytes32 leaf = keccak256(bytes.concat(keccak256(abi.encode(msg.sender, amount))));
        require(MerkleProof.verify(proof, merkleRoot, leaf), "Invalid proof");

        hasClaimed[msg.sender] = true;
        require(token.transfer(msg.sender, amount), "Transfer failed");

        emit Claimed(msg.sender, amount);
    }

    /// @notice Fund the contract (e.g. deployer mints to this contract first).
    function fundedBalance() external view returns (uint256) {
        return token.balanceOf(address(this));
    }
}
