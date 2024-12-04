// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract DecentralizedMLPlatform is Ownable, ReentrancyGuard {
    // Struct to represent a machine learning model
    struct MLModel {
        address creator;
        string modelHash;  // IPFS hash of the model
        uint256 version;
        uint256 totalContributions;
        mapping(address => uint256) contributorStakes;
        bool isActive;
    }

    // Mapping of model ID to MLModel
    mapping(uint256 => MLModel) public models;
    uint256 public modelCount;

    // Events for key actions
    event ModelSubmitted(uint256 indexed modelId, address indexed creator, string modelHash);
    event ModelContribution(uint256 indexed modelId, address indexed contributor, uint256 stakeAmount);
    event ModelEvaluated(uint256 indexed modelId, bool accepted, uint256 performance);

    // Submit a new machine learning model
    function submitModel(string memory _modelHash) public returns (uint256) {
        modelCount++;
        MLModel storage newModel = models[modelCount];
        
        newModel.creator = msg.sender;
        newModel.modelHash = _modelHash;
        newModel.version = 1;
        newModel.isActive = true;

        emit ModelSubmitted(modelCount, msg.sender, _modelHash);
        return modelCount;
    }

    // Contribute to a model's training
    function contributeToModel(uint256 _modelId, uint256 _stakeAmount) public payable nonReentrant {
        require(models[_modelId].isActive, "Model is not active");
        require(msg.value == _stakeAmount, "Stake amount must match sent value");

        models[_modelId].contributorStakes[msg.sender] += _stakeAmount;
        models[_modelId].totalContributions += _stakeAmount;

        emit ModelContribution(_modelId, msg.sender, _stakeAmount);
    }

    // Evaluate and validate a model
    function evaluateModel(
        uint256 _modelId, 
        bool _accepted, 
        uint256 _performanceMetric
    ) public onlyOwner {
        MLModel storage model = models[_modelId];
        require(model.isActive, "Model is not active");

        if (_accepted) {
            // Distribute rewards to contributors
            _distributeRewards(_modelId, _performanceMetric);
        } else {
            // Mark model as inactive if not accepted
            model.isActive = false;
        }

        emit ModelEvaluated(_modelId, _accepted, _performanceMetric);
    }

    // Internal function to distribute rewards
    function _distributeRewards(uint256 _modelId, uint256 _performanceMetric) internal {
        MLModel storage model = models[_modelId];
        uint256 totalReward = address(this).balance * (_performanceMetric / 100);

        // Distribute rewards proportionally to contributions
        for (address contributor : model.contributorStakes) {
            uint256 contributorShare = (model.contributorStakes[contributor] / model.totalContributions) * totalReward;
            payable(contributor).transfer(contributorShare);
        }
    }

    // Withdraw function for contract owner
    function withdraw() public onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }
}
