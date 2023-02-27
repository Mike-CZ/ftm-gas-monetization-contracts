// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";


contract GasMonetization is Ownable {
    event FunderAdded(address indexed funder);
    event FunderRemoved(address indexed funder);
    event FundsAdded(address indexed funder, uint256 amount);
    event FundsWithdrawn(address indexed recipient, uint256 amount);

    /**
     * @notice Map of addresses allowed to fund this contract.
     */
    mapping(address => bool) internal _funders;

    /**
    * @notice Add new funder.
    * @param funder Address of funder.
    */
    function addFunder(address funder) public onlyOwner {
        _funders[funder] = true;
        emit FunderAdded(funder);
    }

    /**
    * @notice Remove funder.
    * @param funder Address of funder.
    */
    function removeFunder(address funder) public onlyOwner {
        delete _funders[funder];
        emit FunderRemoved(funder);
    }

    /**
    * @notice Add funds.
    */
    function addFunds() public payable {
        require(_funders[_msgSender()], "GasMonetization: not funder");
        emit FundsAdded(_msgSender(), msg.value);
    }

    /**
    * @notice Withdraw funds.
    * @param amount Amount to be withdrawn.
    * @param recipient Address of recipient.
    */
    function withdrawFunds(uint256 amount, address recipient) public onlyOwner {
        require(address(this).balance >= amount, "GasMonetization: not enough funds");
        payable(recipient).transfer(amount);
        emit FundsWithdrawn(recipient, amount);
    }

    /**
    * @notice Withdraw all funds.
    * @param recipient Address of recipient.
    */
    function withdrawAllFunds(address recipient) public onlyOwner {
        uint256 balance = address(this).balance;
        payable(recipient).transfer(balance);
        emit FundsWithdrawn(recipient, balance);
    }
}
