// SPDX-License-Identifier: MIT

pragma solidity ^0.8.1;

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
    event WithdrawalRequested(address indexed owner, uint256 blockNumber);
    event WithdrawalCanceled(address indexed owner, uint256 blockNumber);
    event WithdrawalCompleted(address indexed owner, uint256 blockNumber, uint256 amount);
    event WithdrawalBlockLimitUpdated(uint256 limit);
    event WithdrawalConfirmationsLimitUpdated(uint256 limit);
    event WithdrawalConfirmationsDeviationUpdated(uint256 limit);
    event ContractDeployed(
        uint256 withdrawalBlocksFrequencyLimit,
        uint256 confirmationsToMakeWithdrawal,
        uint256 allowedConfirmationsDeviation
    );

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
    * @notice Accounts with this role are eligible to provide data related to rewards withdrawals.
    */
    bytes32 public constant REWARDS_DATA_PROVIDER_ROLE = keccak256("REWARDS_DATA_PROVIDER");

    /**
    * @notice Project represents a project that is eligible to receive funds. This structure consists
    * of project's metadata uri and all related contracts, which will be used to calculate rewards.
    */
    struct Project {
        string metadataUri;
        uint256 lastWithdrawalBlock;
        address[] contracts;
    }

    /**
    * @dev Registry of projects implemented as "project owner address" => "project" mapping.
    */
    mapping(address => Project) internal _projects;

    /**
    * @dev Registry of contracts and owners implemented as "contract address" => "contract owner address" mapping.
    */
    mapping(address => address) internal _contracts_owners;

    /**
    * @dev Last block id when contract was funded.
    */
    uint256 internal _last_block_funds_added = 0;

    /**
    * @dev Restricts withdrawals frequency by specified blocks number.
    */
    uint256 internal _withdrawal_blocks_frequency_limit;

    /**
    * @dev Number of confirmations to complete withdrawal.
    */
    uint256 internal _confirmations_to_make_withdrawal;

    /**
    * @dev Number of allowed deviated confirmations. When this number is exceeded, request is closed.
    */
    uint256 internal _allowed_confirmations_deviation;

    /**
    * @notice PendingWithdrawalRequest represents a pending withdrawal of a project.
    */
    struct PendingWithdrawalRequest {
        uint256 requestedOnBlock;
        uint256 receivedConfirmationsCount;
        // Registry of addresses providing confirmations to prevent confirmations
        // from single address. Implemented as "provider address" => "has provided".
        mapping(address => bool) hasProvided;
        // We also need to keep track of providers addresses to manually remove
        // them from mapping, because deleting object won't affect nested mapping.
        address[] providers;
        // Registry of confirmed values and their count to process withdrawal
        // after agreeing on particular value. Implemented as "value to withdraw" => "confirmations count".
        mapping(uint256 => uint256) confirmedValuesCount;
        // Same as "providers". Keep track of values.
        uint256[] confirmedValues;
    }

    /**
    * @dev Registry of pending withdrawals implemented as "project owner address" => "pending withdrawal" mapping.
    */
    mapping(address => PendingWithdrawalRequest) private _pending_withdrawals;

    /**
    * @notice Contract constructor. It assigns to the creator admin role. Addresses with `DEFAULT_ADMIN_ROLE`
    * are eligible to grant and revoke memberships in particular roles.
    * @param withdrawalBlocksFrequencyLimit Limits how often withdrawals can be done.
    * @param confirmationsToMakeWithdrawal Number of confirmations to process withdrawal.
    * @param allowedConfirmationsDeviation Allowed deviation of different confirmations.
    */
    constructor(
        uint256 withdrawalBlocksFrequencyLimit,
        uint256 confirmationsToMakeWithdrawal,
        uint256 allowedConfirmationsDeviation
    ) public {
        _withdrawal_blocks_frequency_limit = withdrawalBlocksFrequencyLimit;
        _confirmations_to_make_withdrawal = confirmationsToMakeWithdrawal;
        _allowed_confirmations_deviation = allowedConfirmationsDeviation;
        _grantRole(DEFAULT_ADMIN_ROLE, _msgSender());
        emit ContractDeployed(
            withdrawalBlocksFrequencyLimit,
            confirmationsToMakeWithdrawal,
            allowedConfirmationsDeviation
        );
    }

    /**
    * @notice Check owner has pending withdrawal on given block id.
    */
    function hasPendingWithdrawal(address owner, uint256 blockId) public view returns(bool) {
        return _pending_withdrawals[owner].requestedOnBlock == blockId;
    }

    /**
    * @notice Request withdrawal. Only project owner can request.
    */
    function requestWithdrawal() public {
        require(bytes(_projects[_msgSender()].metadataUri).length > 0, "GasMonetization: not project owner");
        uint256 lastProjectWithdrawal = _projects[_msgSender()].lastWithdrawalBlock;
        uint256 lastPendingWithdrawal = _pending_withdrawals[_msgSender()].requestedOnBlock;
        require(
            _last_block_funds_added > 0
            && lastProjectWithdrawal < _last_block_funds_added
            && block.number - lastProjectWithdrawal > _withdrawal_blocks_frequency_limit
            && block.number - lastPendingWithdrawal > _withdrawal_blocks_frequency_limit,
            "GasMonetization: must wait to withdraw"
        );
        // cancel pending withdrawal
        if (lastPendingWithdrawal > 0) {
            _cancelPendingWithdrawal(_msgSender());
            emit WithdrawalCanceled(_msgSender(), lastPendingWithdrawal);
        }
        // prepare new withdrawal
        _pending_withdrawals[_msgSender()].requestedOnBlock = block.number;
        emit WithdrawalRequested(_msgSender(), block.number);
    }

    /**
    * @notice Complete withdrawal.
    * @param owner Address of project owner.
    * @param blockNumber Number of block when request was made.
    * @param amount Amount that owner should receive.
    */
    function completeWithdrawal(address payable owner, uint256 blockNumber, uint256 amount) public {
        require(hasRole(REWARDS_DATA_PROVIDER_ROLE, _msgSender()), "GasMonetization: not rewards data provider");
        require(hasPendingWithdrawal(owner, blockNumber), "GasMonetization: no withdrawal request");
        require(amount > 0, "GasMonetization: no amount to withdraw");
        PendingWithdrawalRequest storage request = _pending_withdrawals[owner];
        require(!request.hasProvided[_msgSender()], "GasMonetization: already confirmed");
        // record received confirmation and mark provider
        request.receivedConfirmationsCount++;
        request.providers.push(_msgSender());
        request.hasProvided[_msgSender()] = true;
        // if amount has not been provided yet, push it into list of values
        if (request.confirmedValuesCount[amount] == 0) {
            request.confirmedValues.push(amount);
        }
        request.confirmedValuesCount[amount]++;
        // make withdrawal when confirmations threshold is reached
        if (request.confirmedValuesCount[amount] >= _confirmations_to_make_withdrawal) {
            _cancelPendingWithdrawal(owner);
            _projects[owner].lastWithdrawalBlock = block.number;
            owner.sendValue(amount);
            emit WithdrawalCompleted(owner, blockNumber, amount);
            return;
        }
        // cancel withdrawal if wee got too many incorrect confirmations
        if (
            request.receivedConfirmationsCount > _confirmations_to_make_withdrawal
            && request.receivedConfirmationsCount - _confirmations_to_make_withdrawal > _allowed_confirmations_deviation
        ) {
            _cancelPendingWithdrawal(owner);
            emit WithdrawalCanceled(owner, blockNumber);
        }
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
            lastWithdrawalBlock: 0,
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
        _last_block_funds_added = block.number;
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
    * @notice Update withdrawal blocks frequency limit.
    * @param limit New limit.
    */
    function updateWithdrawalBlocksFrequencyLimit(uint256 limit) public {
        require(hasRole(DEFAULT_ADMIN_ROLE, _msgSender()), "GasMonetization: not admin");
        _withdrawal_blocks_frequency_limit = limit;
        emit WithdrawalBlockLimitUpdated(limit);
    }

    /**
    * @notice Update withdrawal confirmations limit.
    * @param limit New limit.
    */
    function updateWithdrawalConfirmationsLimit(uint256 limit) public {
        require(hasRole(DEFAULT_ADMIN_ROLE, _msgSender()), "GasMonetization: not admin");
        _confirmations_to_make_withdrawal = limit;
        emit WithdrawalConfirmationsLimitUpdated(limit);
    }

    /**
    * @notice Update withdrawal allowed confirmations deviation.
    * @param limit New limit.
    */
    function updateWithdrawalAllowedConfirmationsDeviation(uint256 limit) public {
        require(hasRole(DEFAULT_ADMIN_ROLE, _msgSender()), "GasMonetization: not admin");
        _allowed_confirmations_deviation = limit;
        emit WithdrawalConfirmationsDeviationUpdated(limit);
    }

    /**
    * @notice Receive function implementation to handle adding funds directly via "send" or "transfer" methods.
    */
    receive() external payable {
        addFunds();
    }

    /**
    * @dev Cancel pending withdrawal.
    * @param owner Pending withdrawal owner.
    */
    function _cancelPendingWithdrawal(address owner) private {
        PendingWithdrawalRequest storage request = _pending_withdrawals[owner];
        // manually clear mappings
        for (uint256 i = 0; i < request.confirmedValues.length; ++i) {
            delete request.confirmedValuesCount[request.confirmedValues[i]];
        }
        for (uint256 i = 0; i < request.providers.length; ++i) {
            delete request.hasProvided[request.providers[i]];
        }
        delete _pending_withdrawals[owner];
    }
}
