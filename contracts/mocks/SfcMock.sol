// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../../interfaces/ISfc.sol";

contract SfcMock is ISfc {
    uint256 _currentEpoch = 0;

    function setEpoch(uint256 epoch) external {
        _currentEpoch = epoch;
    }

    function currentEpoch() external view returns (uint256) {
        return _currentEpoch;
    }
}
