// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../GasMonetization.sol";


contract GasMonetizationMock is GasMonetization {
    constructor(
        address sfcAddress,
        uint256 withdrawalEpochsFrequencyLimit
    ) GasMonetization(sfcAddress, withdrawalEpochsFrequencyLimit) {}

    function getLastEpochFundsAdded() public view returns(uint256) {
        return _last_epoch_funds_added;
    }

    function getProjectMetadataUri(uint256 projectId) public view returns(string memory) {
        return _projects[projectId].metadataUri;
    }

    function getProjectIdOfContract(address contractAddress) public view returns(uint256) {
        return _contracts[contractAddress];
    }

    function getWithdrawalEpochsFrequencyLimit() public view returns(uint256) {
        return _withdrawal_epochs_frequency_limit;
    }
}
