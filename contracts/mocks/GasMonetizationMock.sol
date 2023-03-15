// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../GasMonetization.sol";


contract GasMonetizationMock is GasMonetization {
    constructor(
        address sfcAddress,
        uint256 withdrawalEpochsFrequencyLimit,
        uint256 confirmationsToMakeWithdrawal
    ) GasMonetization(sfcAddress, withdrawalEpochsFrequencyLimit, confirmationsToMakeWithdrawal) {}

    function getLastEpochFundsAdded() public view returns(uint256) {
        return _last_epoch_funds_added;
    }

    function getProjectOwner(uint256 projectId) public view returns(address) {
        return _projects[projectId].owner;
    }

    function getProjectRewardsRecipient(uint256 projectId) public view returns(address) {
        return _projects[projectId].rewardsReceiver;
    }

    function getProjectMetadataUri(uint256 projectId) public view returns(string memory) {
        return _projects[projectId].metadataUri;
    }

    function getProjectActiveFromEpoch(uint256 projectId) public view returns(uint256) {
        return _projects[projectId].activeFromEpoch;
    }

    function getProjectActiveToEpoch(uint256 projectId) public view returns(uint256) {
        return _projects[projectId].activeToEpoch;
    }

    function getProjectIdOfContract(address contractAddress) public view returns(uint256) {
        return _contracts[contractAddress];
    }

    function getWithdrawalEpochsFrequencyLimit() public view returns(uint256) {
        return _withdrawal_epochs_frequency_limit;
    }

    function getWithdrawalConfirmationsLimit() public view returns(uint256) {
        return _confirmations_to_make_withdrawal;
    }

    function getSfcAddress() public view returns(address) {
        return address(_sfc);
    }
}
