// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../GasMonetization.sol";


contract GasMonetizationMock is GasMonetization {
    constructor(
        uint256 withdrawalBlocksFrequencyLimit,
        uint256 confirmationsToMakeWithdrawal,
        uint256 allowedConfirmationsDeviation
    ) GasMonetization(withdrawalBlocksFrequencyLimit, confirmationsToMakeWithdrawal, allowedConfirmationsDeviation) {}

    function getLastBlockFundsAdded() public view returns(uint256) {
        return _last_block_funds_added;
    }

    function getProjectMetadataUri(address owner) public view returns(string memory) {
        return _projects[owner].metadataUri;
    }

    function getProjectContracts(address owner) public view returns(address[] memory) {
        return _projects[owner].contracts;
    }

    function getProjectContractOwner(address contractAddress) public view returns(address) {
        return _contracts_owners[contractAddress];
    }

    function getWithdrawalBlocksFrequencyLimit() public view returns(uint256) {
        return _withdrawal_blocks_frequency_limit;
    }

    function getWithdrawalConfirmationsLimit() public view returns(uint256) {
        return _confirmations_to_make_withdrawal;
    }

    function getWithdrawalAllowedConfirmationsDeviation() public view returns(uint256) {
        return _allowed_confirmations_deviation;
    }
}
