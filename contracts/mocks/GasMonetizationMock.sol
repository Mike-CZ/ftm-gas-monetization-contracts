// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../GasMonetization.sol";


contract GasMonetizationMock is GasMonetization {
    function isFunder(address funder) public view returns(bool) {
        return _funders[funder];
    }
}
