// SPDX-License-Identifier: MIT

pragma solidity ^0.8.1;

import "openzeppelin/contracts/access/AccessControl.sol";
import "openzeppelin/contracts/utils/Address.sol";
import "../interfaces/ISfc.sol";


contract GasMonetization is AccessControl {
    using Address for address payable;

    event FundsAdded(address indexed funder, uint256 amount);
    event FundsWithdrawn(address indexed recipient, uint256 amount);
    event ProjectAdded(
        uint256 indexed projectId,
        address indexed owner,
        address indexed rewardsRecipient,
        string metadataUri,
        uint256 activeFromEpoch,
        address[] contracts
    );
    event ProjectSuspended(uint256 indexed projectId, uint256 suspendedOnEpochNumber);
    event ProjectEnabled(uint256 indexed projectId, uint256 enabledOnEpochNumber);
    event ProjectContractAdded(uint256 indexed projectId, address indexed contractAddress);
    event ProjectContractRemoved(uint256 indexed projectId, address indexed contractAddress);
    event ProjectMetadataUriUpdated(uint256 indexed projectId, string metadataUri);
    event ProjectRewardsRecipientUpdated(uint256 indexed projectId, address recipient);
    event ProjectOwnerUpdated(uint256 indexed projectId, address owner);
    event WithdrawalRequested(uint256 indexed projectId, uint256 requestEpochNumber);
    event WithdrawalCompleted(
        uint256 indexed projectId,
        uint256 requestEpochNumber,
        uint256 withdrawalEpochNumber,
        uint256 amount
    );
    event InvalidWithdrawalAmount(
        uint256 indexed projectId,
        uint256 withdrawalEpochNumber,
        uint256 amount,
        uint256 diffAmount
    );
    event WithdrawalEpochsLimitUpdated(uint256 limit);
    event WithdrawalConfirmationsLimitUpdated(uint256 limit);
    event SfcAddressUpdated(address sfcAddress);
    event ContractDeployed(
        address sfcAddress,
        uint256 withdrawalEpochsFrequencyLimit,
        uint256 confirmationsToMakeWithdrawal
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
        address owner;
        address rewardsRecipient;
        string metadataUri;
        uint256 lastWithdrawalEpoch;
        uint256 activeFromEpoch;
        // Used for disabled projects, when value is 0, then project has no expiration.
        uint256 activeToEpoch;
    }

    /**
    * @dev Registry of projects implemented as "project id" => "project" mapping.
    */
    mapping(uint256 => Project) internal _projects;

    /**
    * @dev Registry of contracts and assigned projects implemented as "contract address" => "project id" mapping.
    */
    mapping(address => uint256) internal _contracts;

    /**
    * @dev Sfc contract used for obtaining current epoch.
    */
    ISfc internal _sfc;

    /**
    * @dev Restricts withdrawals frequency by specified epochs number.
    */
    uint256 internal _withdrawal_epochs_frequency_limit;

    /**
    * @dev Restricts how many confirmations we need to obtain make withdrawal.
    */
    uint256 internal _confirmations_to_make_withdrawal;

    /**
    * @dev Internal counter for identifiers of projects.
    */
    uint256 internal _last_project_id = 0;

    /**
    * @dev Last epoch id when contract was funded.
    */
    uint256 internal _last_epoch_funds_added = 0;

    /**
    * @notice PendingWithdrawalRequest represents a pending withdrawal of a project.
    */
    struct PendingWithdrawalRequest {
        uint256 requestedOnEpoch;
        uint256 receivedConfirmationsCount;
        uint256 receivedConfirmationValue;
        // Array of providers to prevent obtaining confirmations from single address.
        // Mapping can not be used, because it won't get deleted when request is deleted.
        // From solidity docs (https://docs.soliditylang.org/en/develop/types.html#delete):
        // Delete has no effect on whole mappings (as the keys of mappings may be arbitrary and are generally unknown).
        // So if you delete a struct, it will reset all members that are not mappings and also recurse into the members
        // unless they are mappings. However, individual keys and what they map to can be deleted.
        address[] providers;
    }

    /**
    * @dev Registry of pending withdrawals implemented as "project id" => "pending withdrawal" mapping.
    */
    mapping(uint256 => PendingWithdrawalRequest) internal _pending_withdrawals;

    /**
    * @notice Contract constructor. It assigns to the creator admin role. Addresses with `DEFAULT_ADMIN_ROLE`
    * are eligible to grant and revoke memberships in particular roles.
    * @param sfcAddress Address of SFC contract.
    * @param withdrawalEpochsFrequencyLimit Limits how often withdrawals can be done.
    */
    constructor(
        address sfcAddress,
        uint256 withdrawalEpochsFrequencyLimit,
        uint256 confirmationsToMakeWithdrawal
    ) public {
        _sfc = ISfc(sfcAddress);
        _withdrawal_epochs_frequency_limit = withdrawalEpochsFrequencyLimit;
        _confirmations_to_make_withdrawal = confirmationsToMakeWithdrawal;
        _grantRole(DEFAULT_ADMIN_ROLE, _msgSender());
        emit ContractDeployed(sfcAddress, withdrawalEpochsFrequencyLimit, confirmationsToMakeWithdrawal);
    }

    /**
    * @notice Check owner has pending withdrawal on given epoch id.
    * @param projectId Id of project.
    * @param epochId Id of epoch when request was made.
    */
    function hasPendingWithdrawal(uint256 projectId, uint256 epochId) public view returns(bool) {
        return _pending_withdrawals[projectId].requestedOnEpoch == epochId;
    }

    /**
    * @notice Request withdrawal. Only project owner can request.
    * @param projectId Id of project.
    */
    function requestWithdrawal(uint256 projectId) external {
        require(_projects[projectId].owner == _msgSender(), "GasMonetization: not owner");
        require(_pending_withdrawals[projectId].requestedOnEpoch == 0, "GasMonetization: has pending withdrawal");
        require(
            _projects[projectId].activeToEpoch == 0
            || _projects[projectId].lastWithdrawalEpoch < _projects[projectId].activeToEpoch,
            "GasMonetization: project disabled"
        );
        uint256 currentEpoch = _sfc.currentEpoch();
        uint256 lastProjectWithdrawal = _projects[projectId].lastWithdrawalEpoch;
        require(
            _last_epoch_funds_added > 0
            && lastProjectWithdrawal < _last_epoch_funds_added
            && currentEpoch - lastProjectWithdrawal > _withdrawal_epochs_frequency_limit,
            "GasMonetization: must wait to withdraw"
        );
        // prepare new withdrawal
        _pending_withdrawals[projectId].requestedOnEpoch = currentEpoch;
        emit WithdrawalRequested(projectId, currentEpoch);
    }

    /**
    * @notice Complete withdrawal.
    * @param projectId Id of project.
    * @param epochNumber Number of epoch when request was made.
    * @param amount Amount that owner should receive.
    */
    function completeWithdrawal(uint256 projectId, uint256 epochNumber, uint256 amount) external {
        require(hasRole(REWARDS_DATA_PROVIDER_ROLE, _msgSender()), "GasMonetization: not rewards data provider");
        require(hasPendingWithdrawal(projectId, epochNumber), "GasMonetization: no withdrawal request");
        require(amount > 0, "GasMonetization: no amount to withdraw");
        PendingWithdrawalRequest storage request = _pending_withdrawals[projectId];
        // set amount when it is first confirmation
        if (request.receivedConfirmationsCount == 0) {
            request.receivedConfirmationValue = amount;
        } else if (request.receivedConfirmationValue != amount) {
            // otherwise if amount is different, invalidate data we obtained so far
            // and emit event, so next attempt can be made
            emit InvalidWithdrawalAmount(projectId, epochNumber, request.receivedConfirmationValue, amount);
            delete _pending_withdrawals[projectId];
            request.requestedOnEpoch = epochNumber;
            return;
        }
        // validate that provider has not already provided data
        for (uint256 i = 0; i < request.providers.length; ++i) {
            require(request.providers[i] != _msgSender(), "GasMonetization: already provided");
        }
        request.providers.push(_msgSender());
        request.receivedConfirmationsCount++;
        // send amount if confirmations threshold is reached and delete request
        if (request.receivedConfirmationsCount >= _confirmations_to_make_withdrawal) {
            delete _pending_withdrawals[projectId];
            _projects[projectId].lastWithdrawalEpoch = _sfc.currentEpoch();
            payable(_projects[projectId].rewardsRecipient).sendValue(amount);
            emit WithdrawalCompleted(projectId, epochNumber, _projects[projectId].lastWithdrawalEpoch, amount);
        }
    }

    /**
    * @notice Add project into registry.
    * @param owner Address of project owner.
    * @param rewardsRecipient Address of rewards receiver.
    * @param metadataUri Uri of project's metadata.
    * @param contracts Array of related contracts.
    */
    function addProject(
        address owner,
        address rewardsRecipient,
        string calldata metadataUri,
        address[] calldata contracts
    ) external {
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        require(bytes(metadataUri).length > 0, "GasMonetization: empty metadata uri");
        _last_project_id++;
        _projects[_last_project_id] = Project({
            owner: owner,
            rewardsRecipient: rewardsRecipient,
            metadataUri: metadataUri,
            lastWithdrawalEpoch: 0,
            activeFromEpoch: _sfc.currentEpoch(),
            activeToEpoch: 0
        });
        for (uint256 i = 0; i < contracts.length; ++i) {
            require(_contracts[contracts[i]] == 0, "GasMonetization: contract already registered");
            _contracts[contracts[i]] = _last_project_id;
        }
        emit ProjectAdded(
            _last_project_id,
            _projects[_last_project_id].owner,
            _projects[_last_project_id].rewardsRecipient,
            _projects[_last_project_id].metadataUri,
            _projects[_last_project_id].activeFromEpoch,
            contracts
        );
    }

    /**
    * @notice Suspend project from receiving rewards.
    * @param projectId Id of project.
    */
    function suspendProject(uint256 projectId) external {
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        require(_projects[projectId].owner != address(0), "GasMonetization: project does not exist");
        require(_projects[projectId].activeToEpoch == 0, "GasMonetization: project suspended");
        _projects[projectId].activeToEpoch = _sfc.currentEpoch();
        emit ProjectSuspended(projectId, _projects[projectId].activeToEpoch);
    }

    /**
    * @notice Enable project to receive rewards.
    * @param projectId Id of project.
    */
    function enableProject(uint256 projectId) external {
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        require(_projects[projectId].owner != address(0), "GasMonetization: project does not exist");
        require(_projects[projectId].activeToEpoch != 0, "GasMonetization: project active");
        _projects[projectId].activeFromEpoch = _sfc.currentEpoch();
        _projects[projectId].activeToEpoch = 0;
        emit ProjectEnabled(projectId, _projects[projectId].activeFromEpoch);
    }

    /**
    * @notice Add project contract into registry.
    * @param projectId Id of project.
    * @param contractAddress Address of project's contract.
    */
    function addProjectContract(uint256 projectId, address contractAddress) external {
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        require(_projects[projectId].owner != address(0), "GasMonetization: project does not exist");
        require(_contracts[contractAddress] == 0, "GasMonetization: contract already registered");
        _contracts[contractAddress] = projectId;
        emit ProjectContractAdded(projectId, contractAddress);
    }

    /**
    * @notice Remove project contract from registry.
    * @param projectId Id of project.
    * @param contractAddress Address of contract.
    */
    function removeProjectContract(uint256 projectId, address contractAddress) external {
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        require(_projects[projectId].owner != address(0), "GasMonetization: project does not exist");
        require(_contracts[contractAddress] == projectId, "GasMonetization: contract not registered");
        delete _contracts[contractAddress];
        emit ProjectContractRemoved(projectId, contractAddress);
    }

    /**
    * @notice Update project's metadata uri.
    * @param projectId Id of project.
    * @param metadataUri Uri of project's metadata.
    */
    function updateProjectMetadataUri(uint256 projectId, string calldata metadataUri) external {
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        require(_projects[projectId].owner != address(0), "GasMonetization: project does not exist");
        require(bytes(metadataUri).length > 0, "GasMonetization: empty metadata uri");
        _projects[projectId].metadataUri = metadataUri;
        emit ProjectMetadataUriUpdated(projectId, metadataUri);
    }

    /**
    * @notice Update project's rewards recipient.
    * @param projectId Id of project.
    * @param recipient Address of recipient.
    */
    function updateProjectRewardsRecipient(uint256 projectId, address recipient) external {
        require(_projects[projectId].owner == _msgSender(), "GasMonetization: not project owner");
        _projects[projectId].rewardsRecipient = recipient;
        emit ProjectRewardsRecipientUpdated(projectId, recipient);
    }

    /**
    * @notice Update project's owner.
    * @param projectId Id of project.
    * @param owner Address of owner.
    */
    function updateProjectOwner(uint256 projectId, address owner) external {
        require(hasRole(PROJECTS_MANAGER_ROLE, _msgSender()), "GasMonetization: not projects manager");
        require(_projects[projectId].owner != address(0), "GasMonetization: project does not exist");
        _projects[projectId].owner = owner;
        emit ProjectOwnerUpdated(projectId, owner);
    }

    /**
    * @notice Add funds.
    */
    function addFunds() public payable {
        require(hasRole(FUNDER_ROLE, _msgSender()), "GasMonetization: not funder");
        require(msg.value > 0, "GasMonetization: no funds sent");
        _last_epoch_funds_added = _sfc.currentEpoch();
        emit FundsAdded(_msgSender(), msg.value);
    }

    /**
    * @notice Withdraw funds.
    * @param recipient Address of recipient.
    * @param amount Amount to be withdrawn.
    */
    function withdrawFunds(address payable recipient, uint256 amount) external {
        require(hasRole(FUNDS_MANAGER_ROLE, _msgSender()), "GasMonetization: not funds manager");
        recipient.sendValue(amount);
        emit FundsWithdrawn(recipient, amount);
    }

    /**
    * @notice Withdraw all funds.
    * @param recipient Address of recipient.
    */
    function withdrawAllFunds(address payable recipient) external {
        require(hasRole(FUNDS_MANAGER_ROLE, _msgSender()), "GasMonetization: not funds manager");
        uint256 balance = address(this).balance;
        recipient.sendValue(balance);
        emit FundsWithdrawn(recipient, balance);
    }

    /**
    * @notice Update withdrawal epochs frequency limit.
    * @param limit New limit.
    */
    function updateWithdrawalEpochsFrequencyLimit(uint256 limit) external {
        require(hasRole(DEFAULT_ADMIN_ROLE, _msgSender()), "GasMonetization: not admin");
        _withdrawal_epochs_frequency_limit = limit;
        emit WithdrawalEpochsLimitUpdated(limit);
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
    * @notice Update sfc address.
    * @param sfc New sfc address.
    */
    function updateSfcAddress(address sfc) external {
        require(hasRole(DEFAULT_ADMIN_ROLE, _msgSender()), "GasMonetization: not admin");
        _sfc = ISfc(sfc);
        emit SfcAddressUpdated(sfc);
    }

    /**
    * @notice Receive function implementation to handle adding funds directly via "send" or "transfer" methods.
    */
    receive() external payable {
        addFunds();
    }
}
