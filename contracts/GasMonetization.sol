// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/AccessControl.sol";
import "openzeppelin/contracts/utils/Address.sol";


contract GasMonetization is AccessControl {
    using Address for address payable;

    /**
    * @notice Accounts with this role are eligible to fund this contract.
    */
    bytes32 public constant FUNDER_ROLE = keccak256("FUNDER");
    /**
    * @notice Accounts with this role are eligible to handle funds of this contract.
    */
    bytes32 public constant FUNDS_MANAGER_ROLE = keccak256("FUNDS_MANAGER");

    /**
    * @notice Accounts with this role are eligible to manage projects.
    */
    bytes32 public constant PROJECTS_MANAGER_ROLE = keccak256("PROJECTS_MANAGER");

    event FunderAdded(address indexed funder);
    event FunderRemoved(address indexed funder);
    event FundsAdded(address indexed funder, uint256 amount);
    event FundsWithdrawn(address indexed recipient, uint256 amount);

    /**
    * @notice Project represents a project that is eligible to receive funds. This structure consists
    * of project's metadata uri and all related contracts, which will be used to calculate rewards.
    */
    struct Project {
        string metadataUri;
        address[] contracts;
    }

    /**
    * @notice Registry of projects implemented as "project owner" => "project" mapping.
    */
    mapping(address => Project) private _projects;

    /**
    * @notice Contract constructor. It assigns to the creator admin role. Addresses with `DEFAULT_ADMIN_ROLE`
    * are eligible to grant and revoke memberships in particular roles.
    */
    constructor() public {
        _grantRole(DEFAULT_ADMIN_ROLE, _msgSender());
    }

    /**
    * @notice Project into registry.
    */
    function addProject(address owner, string metadataUri, address[] contracts) {
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        require(_projects[owner].contracts.length == 0, "GasMonetization: project exists");
        _projects[owner] = Project({
            metadataUri: metadataUri,
            contracts: contracts
        });
    }

    /**
    * @notice Add funds.
    */
    function addFunds() public payable {
        require(hasRole(FUNDER_ROLE, _msgSender()), "GasMonetization: not funder");
        emit FundsAdded(_msgSender(), msg.value);
    }

    /**
    * @notice Withdraw funds.
    * @param recipient Address of recipient.
    * @param amount Amount to be withdrawn.
    */
    function withdrawFunds(address payable recipient, uint256 amount) public {
        require(hasRole(FUNDS_MANAGER_ROLE, _msgSender()), "GasMonetization: not funds manager");
        recipient.sendValue(amount);
        emit FundsWithdrawn(recipient, amount);
    }

    /**
    * @notice Withdraw all funds.
    * @param recipient Address of recipient.
    */
    function withdrawAllFunds(address payable recipient) public {
        require(hasRole(FUNDS_MANAGER_ROLE, _msgSender()), "GasMonetization: not funds manager");
        uint256 balance = address(this).balance;
        recipient.sendValue(balance);
        emit FundsWithdrawn(recipient, balance);
    }

    /**
    * @notice Receive function implementation to handle adding funds directly via "send" or "transfer" methods.
    */
    receive() external payable {
        addFunds();
    }
}
