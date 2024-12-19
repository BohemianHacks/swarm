// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DecentralizedML {
    // State variables
    address public owner;
    mapping(address => uint256) public contributions;
    uint256 public totalContributions;
    bytes32 public currentModelHash;
    uint256 public rewardPool;

    // Events
    event DataSubmitted(address indexed contributor, uint256 amount);
    event ModelTrained(bytes32 indexed modelHash);
    event InferenceRequested(bytes32 indexed requestId);

    // Constructor
    constructor() {
        owner = msg.sender;
    }

    // Modifier to restrict access to owner
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    // Function to submit data for training
    function submitData(bytes calldata data) external {
        contributions[msg.sender] += 1;
        totalContributions++;
        emit DataSubmitted(msg.sender, 1);
    }

    // Function to train the model (placeholder for actual training logic)
    function trainModel(bytes32 modelHash) external onlyOwner {
        currentModelHash = modelHash;
        emit ModelTrained(modelHash);
    }

    // Function to request model inference
    function requestInference(bytes calldata inputData) external view returns (bytes memory) {
        // Here you would call an off-chain service or another contract for actual inference
        bytes memory placeholder = "Inference result";
        emit InferenceRequested(keccak256(abi.encodePacked(msg.sender, inputData)));
        return placeholder;
    }

    // Function to add rewards to the pool
    function addReward(uint256 amount) external onlyOwner {
        rewardPool += amount;
    }

    // Function to distribute rewards based on contributions
    function distributeRewards() external onlyOwner {
        require(rewardPool > 0, "No rewards to distribute");
        uint256 totalShares = totalContributions;
        for (address contributor in contributions) {
            if (contributions[contributor] > 0) {
                uint256 share = (contributions[contributor] * rewardPool) / totalShares;
                // Transfer the reward here, typically you'd use a token transfer function
                // token.transfer(msg.sender, share);
                rewardPool -= share;
            }
        }
        totalContributions = 0; // Reset contributions
    }
}
