// SPDX-License-Identifier: MIT

pragma solidity ^0.8.1;

interface ISfc {
   // we only need to get current epoch from sfc
   function currentEpoch() external view returns (uint256);
}