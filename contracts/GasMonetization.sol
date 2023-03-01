// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/AccessControl.sol";
import "openzeppelin/contracts/utils/Address.sol";


contract GasMonetization is AccessControl {
    using Address for address payable;

    event FundsAdded(address indexed funder, uint256 amount);
    event FundsWithdrawn(address indexed recipient, uint256 amount);
    event ProjectAdded(address indexed owner, string metadataUri, address[] contracts);
    event ProjectRemoved(address indexed owner);
    event ProjectContractAdded(address indexed owner, address indexed contractAddress);
    event ProjectContractRemoved(address indexed owner, address indexed contractAddress);
    event ProjectContractsSet(address indexed owner, address[] contracts);
    event ProjectMetadataUriUpdated(address indexed owner, string metadataUri);

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

    /**
    * @notice Project represents a project that is eligible to receive funds. This structure consists
    * of project's metadata uri and all related contracts, which will be used to calculate rewards.
    */
    struct Project {
        string metadataUri;
        uint256 lastWithdrawnEpoch;
        address[] contracts;
    }

    /**
    * @notice Registry of projects implemented as "project owner address" => "project" mapping.
    */
    mapping(address => Project) private _projects;


    /**
    * @notice Registry of contracts and owners implemented as "contract address" => "contract owner address" mapping.
    */
    mapping(address => address) private _contracts_owners;

    /**
    * @notice Contract constructor. It assigns to the creator admin role. Addresses with `DEFAULT_ADMIN_ROLE`
    * are eligible to grant and revoke memberships in particular roles.
    */
    constructor() public {
        _grantRole(DEFAULT_ADMIN_ROLE, _msgSender());
    }

    /**
    * @notice Get project metadata uri.
    * @param owner Address of project owner.
    */
    function getProjectMetadataUri(address owner) public view returns(string memory) {
        return _projects[owner].metadataUri;
    }

    /**
    * @notice Get project metadata uri.
    * @param owner Address of project owner.
    */
    function getProjectContracts(address owner) public view returns(address[] memory) {
        return _projects[owner].contracts;
    }

    /**
    * @notice Get contract project owner address.
    * @param contractAddress Address of contract.
    */
    function getContractProjectOwner(address contractAddress) public view returns(address) {
        return _contracts_owners[contractAddress];
    }

    /**
    * @notice Add project into registry.
    * @param owner Address of project owner.
    * @param metadataUri Uri of project's metadata.
    * @param contracts Array of related contracts.
    */
    function addProject(address owner, string calldata metadataUri, address[] calldata contracts) public {
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        require(bytes(metadataUri).length > 0, "GasMonetization: empty metadata uri");
        require(bytes(_projects[owner].metadataUri).length == 0, "GasMonetization: project exists");
        _projects[owner] = Project({
            metadataUri: metadataUri,
            lastWithdrawnEpoch: 0,
            contracts: contracts
        });
        for (uint256 i = 0; i < contracts.length; ++i) {
            require(_contracts_owners[contracts[i]] == address(0), "GasMonetization: contract already registered");
            _contracts_owners[contracts[i]] = owner;
        }
        emit ProjectAdded(owner, _projects[owner].metadataUri, _projects[owner].contracts);
    }

    /**
    * @notice Remove project from registry.
    * @param owner Address of project owner.
    */
    function removeProject(address owner) public {
        // TODO: should be owner allowed to remove own project?
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        require(bytes(_projects[owner].metadataUri).length > 0, "GasMonetization: project does not exist");
        for (uint256 i = 0; i < _projects[owner].contracts.length; ++i) {
            delete _contracts_owners[_projects[owner].contracts[i]];
        }
        delete _projects[owner];
        emit ProjectRemoved(owner);
    }

    /**
    * @notice Add project contract into registry.
    * @param owner Address of project owner.
    * @param contractAddress Address of project's contract.
    */
    function addProjectContract(address owner, address contractAddress) public {
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        require(bytes(_projects[owner].metadataUri).length > 0, "GasMonetization: project does not exist");
        require(_contracts_owners[contractAddress] == address(0), "GasMonetization: contract already registered");
        _projects[owner].contracts.push(contractAddress);
        _contracts_owners[contractAddress] = owner;
        emit ProjectContractAdded(owner, contractAddress);
    }

    /**
    * @notice Remove project contract from registry.
    * @param owner Address of project owner.
    * @param contractAddress Address of contract.
    */
    function removeProjectContract(address owner, address contractAddress) public {
        // TODO: should be owner allowed to remove own contract?
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        require(bytes(_projects[owner].metadataUri).length > 0, "GasMonetization: project does not exist");
        require(_contracts_owners[contractAddress] == owner, "GasMonetization: contract not registered");
        // make copy of current contracts and empty storage values
        address[] memory contracts = _projects[owner].contracts;
        delete _projects[owner].contracts;
        delete _contracts_owners[contractAddress];
        // re-insert values without deleted contract
        for (uint256 i = 0; i < contracts.length; ++i) {
            if (contracts[i] != contractAddress) {
                _projects[owner].contracts.push(contracts[i]);
            }
        }
        emit ProjectContractRemoved(owner, contractAddress);
    }

    /**
    * @notice Set project contracts into registry.
    * @param owner Address of project owner.
    * @param contracts Addresses of contracts to be set.
    */
    function setProjectContracts(address owner, address[] calldata contracts) public {
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        // remove all contracts ownerships for given owner - it will be re-set in the next step
        for (uint256 i = 0; i < _projects[owner].contracts.length; ++i) {
            delete _contracts_owners[_projects[owner].contracts[i]];
        }
        // make sure contracts are not already registered
        for (uint256 i = 0; i < contracts.length; ++i) {
            require(_contracts_owners[contracts[i]] == address(0), "GasMonetization: project already registered");
            // set contract ownership
            _contracts_owners[contracts[i]] = owner;
        }
        _projects[owner].contracts = contracts;
        emit ProjectContractsSet(owner, _projects[owner].contracts);
    }

    /**
    * @notice Update project's metadata uri.
    * @param owner Address of project owner.
    * @param metadataUri Uri of project's metadata.
    */
    function updateProjectMetadataUri(address owner, string calldata metadataUri) public {
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        require(bytes(_projects[owner].metadataUri).length > 0, "GasMonetization: project does not exist");
        require(bytes(metadataUri).length > 0, "GasMonetization: empty metadata uri");
        _projects[owner].metadataUri = metadataUri;
        emit ProjectMetadataUriUpdated(owner, metadataUri);
    }

    /**
    * @notice Add funds.
    */
    function addFunds() public payable {
        require(hasRole(FUNDER_ROLE, _msgSender()), "GasMonetization: not funder");
        require(msg.value > 0, "GasMonetization: no funds sent");
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
