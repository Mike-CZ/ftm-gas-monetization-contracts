from brownie import reverts, ZERO_ADDRESS
from brownie.network.transaction import TransactionReceipt
from brownie.test import given, strategy
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from hypothesis import settings
from typing import Callable
from utils.constants import ProjectParams


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_project_can_be_added(
        gas_monetization: ProjectContract,
        sfc: ProjectContract,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    tx: TransactionReceipt = gas_monetization.addProject(
        owner, rewards_recipient, ProjectParams.metadata_uri, ProjectParams.contracts, {'from': projects_manager}
    )
    assert tx.events['ProjectAdded'] is not None
    assert tx.events['ProjectAdded']['projectId'] == ProjectParams.project_id
    assert tx.events['ProjectAdded']['owner'] == owner
    assert tx.events['ProjectAdded']['rewardsRecipient'] == rewards_recipient
    assert tx.events['ProjectAdded']['metadataUri'] == ProjectParams.metadata_uri
    assert tx.events['ProjectAdded']['activeFromEpoch'] == sfc.currentEpoch()
    assert tx.events['ProjectAdded']['contracts'] == ProjectParams.contracts
    assert gas_monetization.getProjectOwner(ProjectParams.project_id) == owner
    assert gas_monetization.getProjectRewardsRecipient(ProjectParams.project_id) == rewards_recipient
    assert gas_monetization.getProjectMetadataUri(ProjectParams.project_id) == ProjectParams.metadata_uri
    for addr in ProjectParams.contracts:
        assert gas_monetization.getProjectIdOfContract(addr) == ProjectParams.project_id


@given(non_projects_manager=strategy('address'))
@settings(max_examples=10)
def test_non_project_manager_cannot_add_project(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount,
        non_projects_manager: LocalAccount
) -> None:
    if projects_manager.address == non_projects_manager.address:
        return
    with reverts("GasMonetization: not projects manager"):
        gas_monetization.addProject(
            non_projects_manager, non_projects_manager, ProjectParams.metadata_uri,
            ProjectParams.contracts, {'from': non_projects_manager}
        )


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_project_cannot_be_added_with_empty_metadata(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    with reverts("GasMonetization: empty metadata uri"):
        gas_monetization.addProject(
            owner, rewards_recipient, '', ProjectParams.contracts, {'from': projects_manager}
        )


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
    wannabe_owner=strategy('address')
)
@settings(max_examples=10)
def test_project_cannot_be_added_when_contract_already_registered(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        wannabe_owner: LocalAccount
) -> None:
    setup_project(owner, rewards_recipient)
    with reverts("GasMonetization: contract already registered"):
        gas_monetization.addProject(
            wannabe_owner, wannabe_owner, ProjectParams.metadata_uri,
            ProjectParams.contracts[1:], {'from': projects_manager}
        )


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_project_can_be_suspended(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        set_epoch_number: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    setup_project(owner, rewards_recipient)
    set_epoch_number(50)
    tx: TransactionReceipt = gas_monetization.suspendProject(ProjectParams.project_id, {'from': projects_manager})
    assert tx.events['ProjectSuspended'] is not None
    assert tx.events['ProjectSuspended']['projectId'] == ProjectParams.project_id
    assert tx.events['ProjectSuspended']['suspendedOnEpochNumber'] == 50
    assert gas_monetization.getProjectActiveToEpoch(ProjectParams.project_id) == 50


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
    non_projects_manager=strategy('address')
)
@settings(max_examples=10)
def test_non_project_manager_cannot_suspend_project(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        non_projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    if projects_manager.address == non_projects_manager.address:
        return
    setup_project(owner, rewards_recipient)
    with reverts("GasMonetization: not projects manager"):
        gas_monetization.suspendProject(ProjectParams.project_id, {'from': non_projects_manager})


def test_non_existing_project_cannot_be_suspended(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount
) -> None:
    with reverts("GasMonetization: project does not exist"):
        gas_monetization.suspendProject(ProjectParams.project_id, {'from': projects_manager})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_suspended_project_cannot_be_suspended(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        set_epoch_number: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    setup_project(owner, rewards_recipient)
    set_epoch_number(50)
    gas_monetization.suspendProject(ProjectParams.project_id, {'from': projects_manager})
    with reverts("GasMonetization: project suspended"):
        gas_monetization.suspendProject(ProjectParams.project_id, {'from': projects_manager})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_project_can_be_enabled(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        set_epoch_number: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    setup_project(owner, rewards_recipient)
    set_epoch_number(50)
    gas_monetization.suspendProject(ProjectParams.project_id, {'from': projects_manager})
    set_epoch_number(100)
    tx: TransactionReceipt = gas_monetization.enableProject(ProjectParams.project_id, {'from': projects_manager})
    assert tx.events['ProjectEnabled'] is not None
    assert tx.events['ProjectEnabled']['projectId'] == ProjectParams.project_id
    assert tx.events['ProjectEnabled']['enabledOnEpochNumber'] == 100
    assert gas_monetization.getProjectActiveFromEpoch(ProjectParams.project_id) == 100
    assert gas_monetization.getProjectActiveToEpoch(ProjectParams.project_id) == 0


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
    non_projects_manager=strategy('address')
)
@settings(max_examples=10)
def test_non_project_manager_cannot_enable_project(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        set_epoch_number: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        non_projects_manager: LocalAccount
) -> None:
    if projects_manager.address == non_projects_manager.address:
        return
    setup_project(owner, rewards_recipient)
    set_epoch_number(50)
    gas_monetization.suspendProject(ProjectParams.project_id, {'from': projects_manager})
    set_epoch_number(100)
    with reverts("GasMonetization: not projects manager"):
        gas_monetization.enableProject(ProjectParams.project_id, {'from': non_projects_manager})


def test_non_existing_project_cannot_be_enabled(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount
) -> None:
    with reverts("GasMonetization: project does not exist"):
        gas_monetization.enableProject(ProjectParams.project_id, {'from': projects_manager})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_active_project_cannot_be_enabled(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
) -> None:
    setup_project(owner, rewards_recipient)
    with reverts("GasMonetization: project active"):
        gas_monetization.enableProject(ProjectParams.project_id, {'from': projects_manager})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_project_contract_can_be_added(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    contract: str = '0xc41BE986CFb594156b08CFd272Cbf8FF52E4D2eD'
    setup_project(owner, rewards_recipient)
    tx: TransactionReceipt = gas_monetization.addProjectContract(
        ProjectParams.project_id, contract, {'from': projects_manager}
    )
    assert tx.events['ProjectContractAdded'] is not None
    assert tx.events['ProjectContractAdded']['projectId'] == ProjectParams.project_id
    assert tx.events['ProjectContractAdded']['contractAddress'] == contract
    assert gas_monetization.getProjectIdOfContract(contract) == ProjectParams.project_id


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
    non_projects_manager=strategy('address')
)
@settings(max_examples=10)
def test_non_project_manager_cannot_add_project_contract(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        non_projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    if projects_manager.address == non_projects_manager.address:
        return
    contract: str = '0xc41BE986CFb594156b08CFd272Cbf8FF52E4D2eD'
    setup_project(owner, rewards_recipient)
    with reverts("GasMonetization: not projects manager"):
        gas_monetization.addProjectContract(ProjectParams.project_id, contract, {'from': non_projects_manager})


def test_cannot_add_project_contract_when_project_does_not_exist(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount
) -> None:
    contract: str = '0xc41BE986CFb594156b08CFd272Cbf8FF52E4D2eD'
    with reverts("GasMonetization: project does not exist"):
        gas_monetization.addProjectContract(ProjectParams.project_id, contract, {'from': projects_manager})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_cannot_add_project_contract_when_contract_already_registered(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    setup_project(owner, rewards_recipient)
    with reverts("GasMonetization: contract already registered"):
        gas_monetization.addProjectContract(
            ProjectParams.project_id, ProjectParams.contracts[0], {'from': projects_manager}
        )


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_project_contract_can_be_removed(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    setup_project(owner, rewards_recipient)
    tx: TransactionReceipt = gas_monetization.removeProjectContract(
        ProjectParams.project_id, ProjectParams.contracts[0], {'from': projects_manager}
    )
    assert tx.events['ProjectContractRemoved'] is not None
    assert tx.events['ProjectContractRemoved']['projectId'] == ProjectParams.project_id
    assert tx.events['ProjectContractRemoved']['contractAddress'] == ProjectParams.contracts[0]
    assert gas_monetization.getProjectIdOfContract(ProjectParams.contracts[0]) == 0


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
    non_projects_manager=strategy('address')
)
@settings(max_examples=10)
def test_non_project_manager_cannot_remove_project_contract(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        non_projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    if projects_manager.address == non_projects_manager.address:
        return
    setup_project(owner, rewards_recipient)
    with reverts("GasMonetization: not projects manager"):
        gas_monetization.removeProjectContract(
            ProjectParams.project_id, ProjectParams.contracts[0], {'from': non_projects_manager}
        )


def test_cannot_remove_project_contract_when_project_does_not_exist(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount
) -> None:
    with reverts("GasMonetization: project does not exist"):
        gas_monetization.removeProjectContract(
            ProjectParams.project_id, ProjectParams.contracts[0], {'from': projects_manager}
        )


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_cannot_remove_project_contract_when_contract_not_registered(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    contract: str = '0xc41BE986CFb594156b08CFd272Cbf8FF52E4D2eD'
    setup_project(owner, rewards_recipient)
    with reverts("GasMonetization: contract not registered"):
        gas_monetization.removeProjectContract(ProjectParams.project_id, contract, {'from': projects_manager})

@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_project_metadata_uri_can_be_updated(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    setup_project(owner, rewards_recipient)
    tx: TransactionReceipt = gas_monetization.updateProjectMetadataUri(
        ProjectParams.project_id, 'new-uri', {'from': projects_manager}
    )
    assert tx.events['ProjectMetadataUriUpdated'] is not None
    assert tx.events['ProjectMetadataUriUpdated']['projectId'] == ProjectParams.project_id
    assert tx.events['ProjectMetadataUriUpdated']['metadataUri'] == 'new-uri'
    assert gas_monetization.getProjectMetadataUri(ProjectParams.project_id) == 'new-uri'


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
    non_projects_manager=strategy('address')
)
@settings(max_examples=10)
def test_non_project_manager_cannot_update_project_metadata_uri(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        non_projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    if projects_manager.address == non_projects_manager.address:
        return
    setup_project(owner, rewards_recipient)
    with reverts("GasMonetization: not projects manager"):
        gas_monetization.updateProjectMetadataUri(ProjectParams.project_id, 'new-uri', {'from': non_projects_manager})


def test_cannot_update_project_metadata_uri_when_project_does_not_exist(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount
) -> None:
    with reverts("GasMonetization: project does not exist"):
        gas_monetization.updateProjectMetadataUri(ProjectParams.project_id, 'new-uri', {'from': projects_manager})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_cannot_update_project_metadata_uri_when_is_empty(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    setup_project(owner, rewards_recipient)
    with reverts("GasMonetization: empty metadata uri"):
        gas_monetization.updateProjectMetadataUri(ProjectParams.project_id, '', {'from': projects_manager})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
    new_rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_project_rewards_recipient_can_be_updated(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        new_rewards_recipient: LocalAccount
) -> None:
    setup_project(owner, rewards_recipient)
    tx: TransactionReceipt = gas_monetization.updateProjectRewardsRecipient(
        ProjectParams.project_id, new_rewards_recipient, {'from': owner}
    )
    assert tx.events['ProjectRewardsRecipientUpdated'] is not None
    assert tx.events['ProjectRewardsRecipientUpdated']['projectId'] == ProjectParams.project_id
    assert tx.events['ProjectRewardsRecipientUpdated']['recipient'] == new_rewards_recipient
    assert gas_monetization.getProjectRewardsRecipient(ProjectParams.project_id) == new_rewards_recipient


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
    non_owner=strategy('address')
)
@settings(max_examples=10)
def test_non_owner_cannot_change_rewards_recipient(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        non_owner: LocalAccount
) -> None:
    if owner.address == non_owner.address:
        return
    setup_project(owner, rewards_recipient)
    with reverts('GasMonetization: not project owner'):
        gas_monetization.updateProjectRewardsRecipient(ProjectParams.project_id, non_owner, {'from': non_owner})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
    new_owner=strategy('address')
)
@settings(max_examples=10)
def test_project_owner_can_be_updated(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        new_owner: LocalAccount
) -> None:
    setup_project(owner, rewards_recipient)
    tx: TransactionReceipt = gas_monetization.updateProjectOwner(
        ProjectParams.project_id, new_owner, {'from': projects_manager}
    )
    assert tx.events['ProjectOwnerUpdated'] is not None
    assert tx.events['ProjectOwnerUpdated']['projectId'] == ProjectParams.project_id
    assert tx.events['ProjectOwnerUpdated']['owner'] == new_owner
    assert gas_monetization.getProjectOwner(ProjectParams.project_id) == new_owner


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
    new_owner=strategy('address'),
    non_projects_manager=strategy('address')
)
@settings(max_examples=10)
def test_non_project_manager_cannot_update_project_owner(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        non_projects_manager: LocalAccount,
        owner: LocalAccount,
        new_owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    if projects_manager.address == non_projects_manager.address:
        return
    setup_project(owner, rewards_recipient)
    with reverts("GasMonetization: not projects manager"):
        gas_monetization.updateProjectOwner(ProjectParams.project_id, new_owner, {'from': non_projects_manager})


@given(new_owner=strategy('address'))
def test_cannot_update_project_owner_when_project_does_not_exist(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount,
        new_owner: LocalAccount
) -> None:
    with reverts("GasMonetization: project does not exist"):
        gas_monetization.updateProjectOwner(ProjectParams.project_id, new_owner, {'from': projects_manager})

