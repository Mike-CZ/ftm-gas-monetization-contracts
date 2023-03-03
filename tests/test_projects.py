from brownie import reverts, ZERO_ADDRESS
from brownie.network.transaction import TransactionReceipt
from brownie.test import given, strategy
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from hypothesis import settings
from typing import Callable
from utils.constants import ProjectParams


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_project_can_be_added(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    tx: TransactionReceipt = gas_monetization.addProject(
        owner, ProjectParams.metadata_uri, ProjectParams.contracts, {'from': projects_manager}
    )
    assert tx.events['ProjectAdded'] is not None
    assert tx.events['ProjectAdded']['owner'] == owner
    assert tx.events['ProjectAdded']['metadataUri'] == ProjectParams.metadata_uri
    assert tx.events['ProjectAdded']['contracts'] == ProjectParams.contracts
    assert gas_monetization.getProjectMetadataUri(owner) == ProjectParams.metadata_uri
    assert gas_monetization.getProjectContracts(owner) == ProjectParams.contracts
    for addr in ProjectParams.contracts:
        assert gas_monetization.getProjectContractOwner(addr) == owner


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
            non_projects_manager, ProjectParams.metadata_uri, ProjectParams.contracts, {'from': non_projects_manager}
        )


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_project_cannot_be_added_with_empty_metadata(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    with reverts("GasMonetization: empty metadata uri"):
        gas_monetization.addProject(
            owner, '', ProjectParams.contracts, {'from': projects_manager}
        )


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_project_cannot_be_added_when_already_exists(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    setup_project(owner)
    with reverts("GasMonetization: project exists"):
        gas_monetization.addProject(
            owner, ProjectParams.metadata_uri, ProjectParams.contracts, {'from': projects_manager}
        )


@given(
    owner=strategy('address'),
    wannabe_owner=strategy('address')
)
@settings(max_examples=10)
def test_project_cannot_be_added_when_contract_already_registered(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        wannabe_owner: LocalAccount
) -> None:
    if owner.address == wannabe_owner.address:
        return
    setup_project(owner)
    with reverts("GasMonetization: contract already registered"):
        gas_monetization.addProject(
            wannabe_owner, ProjectParams.metadata_uri, ProjectParams.contracts[1:], {'from': projects_manager}
        )


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_project_can_be_removed(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    setup_project(owner)
    tx: TransactionReceipt = gas_monetization.removeProject(owner, {'from': projects_manager})
    assert tx.events['ProjectRemoved'] is not None
    assert tx.events['ProjectRemoved']['owner'] == owner
    assert gas_monetization.getProjectMetadataUri(owner) == ''
    assert gas_monetization.getProjectContracts(owner) == []
    for addr in ProjectParams.contracts:
        assert gas_monetization.getProjectContractOwner(addr) == ZERO_ADDRESS


@given(
    owner=strategy('address'),
    non_projects_manager=strategy('address')
)
@settings(max_examples=10)
def test_non_project_manager_cannot_remove_project(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        non_projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    if projects_manager.address == non_projects_manager.address:
        return
    setup_project(owner)
    with reverts("GasMonetization: not projects manager"):
        gas_monetization.removeProject(owner, {'from': non_projects_manager})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_non_existing_project_cannot_be_removed(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    with reverts("GasMonetization: project does not exist"):
        gas_monetization.removeProject(owner, {'from': projects_manager})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_project_contract_can_be_added(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    contract: str = '0xc41BE986CFb594156b08CFd272Cbf8FF52E4D2eD'
    setup_project(owner)
    tx: TransactionReceipt = gas_monetization.addProjectContract(owner, contract, {'from': projects_manager})
    assert tx.events['ProjectContractAdded'] is not None
    assert tx.events['ProjectContractAdded']['owner'] == owner
    assert tx.events['ProjectContractAdded']['contractAddress'] == contract
    assert gas_monetization.getProjectContractOwner(contract) == owner
    assert contract in gas_monetization.getProjectContracts(owner)


@given(
    owner=strategy('address'),
    non_projects_manager=strategy('address')
)
@settings(max_examples=10)
def test_non_project_manager_cannot_add_project_contract(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        non_projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    if projects_manager.address == non_projects_manager.address:
        return
    contract: str = '0xc41BE986CFb594156b08CFd272Cbf8FF52E4D2eD'
    setup_project(owner)
    with reverts("GasMonetization: not projects manager"):
        gas_monetization.addProjectContract(owner, contract, {'from': non_projects_manager})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_cannot_add_project_contract_when_project_does_not_exist(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    contract: str = '0xc41BE986CFb594156b08CFd272Cbf8FF52E4D2eD'
    with reverts("GasMonetization: project does not exist"):
        gas_monetization.addProjectContract(owner, contract, {'from': projects_manager})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_cannot_add_project_contract_when_contract_already_registered(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    setup_project(owner)
    with reverts("GasMonetization: contract already registered"):
        gas_monetization.addProjectContract(owner, ProjectParams.contracts[0], {'from': projects_manager})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_project_contract_can_be_removed(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    setup_project(owner)
    tx: TransactionReceipt = gas_monetization.removeProjectContract(owner, ProjectParams.contracts[0], {'from': projects_manager})
    assert tx.events['ProjectContractRemoved'] is not None
    assert tx.events['ProjectContractRemoved']['owner'] == owner
    assert tx.events['ProjectContractRemoved']['contractAddress'] == ProjectParams.contracts[0]
    assert gas_monetization.getProjectContractOwner(ProjectParams.contracts[0]) == ZERO_ADDRESS
    assert gas_monetization.getProjectContracts(owner) == ProjectParams.contracts[1:]


@given(
    owner=strategy('address'),
    non_projects_manager=strategy('address')
)
@settings(max_examples=10)
def test_non_project_manager_cannot_remove_project_contract(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        non_projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    if projects_manager.address == non_projects_manager.address:
        return
    setup_project(owner)
    with reverts("GasMonetization: not projects manager"):
        gas_monetization.removeProjectContract(owner, ProjectParams.contracts[0], {'from': non_projects_manager})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_cannot_remove_project_contract_when_project_does_not_exist(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    with reverts("GasMonetization: project does not exist"):
        gas_monetization.removeProjectContract(owner, ProjectParams.contracts[0], {'from': projects_manager})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_cannot_remove_project_contract_when_contract_not_registered(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    contract: str = '0xc41BE986CFb594156b08CFd272Cbf8FF52E4D2eD'
    setup_project(owner)
    with reverts("GasMonetization: contract not registered"):
        gas_monetization.removeProjectContract(owner, contract, {'from': projects_manager})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_project_contracts_can_be_set(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    # create list of contracts without the first one - it will be checked that this contract got removed
    contracts: list[str] = ProjectParams.contracts[1:]
    # add new contract to the list
    contracts.append('0xc41BE986CFb594156b08CFd272Cbf8FF52E4D2eD')
    setup_project(owner)
    tx: TransactionReceipt = gas_monetization.setProjectContracts(owner, contracts, {'from': projects_manager})
    assert tx.events['ProjectContractsSet'] is not None
    assert tx.events['ProjectContractsSet']['owner'] == owner
    assert tx.events['ProjectContractsSet']['contracts'] == contracts
    assert gas_monetization.getProjectContracts(owner) == contracts
    for addr in contracts:
        assert gas_monetization.getProjectContractOwner(addr) == owner
    assert gas_monetization.getProjectContractOwner(ProjectParams.contracts[0]) == ZERO_ADDRESS


@given(
    owner=strategy('address'),
    non_projects_manager=strategy('address')
)
@settings(max_examples=10)
def test_non_project_manager_cannot_set_project_contracts(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        non_projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    if projects_manager.address == non_projects_manager.address:
        return
    contracts: list[str] = ProjectParams.contracts[1:]
    contracts.append('0xc41BE986CFb594156b08CFd272Cbf8FF52E4D2eD')
    setup_project(owner)
    with reverts("GasMonetization: not projects manager"):
        gas_monetization.setProjectContracts(owner, contracts, {'from': non_projects_manager})


@given(
    owner=strategy('address'),
    wannabe_owner=strategy('address')
)
@settings(max_examples=10)
def test_set_project_contracts_when_already_registered(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount,
        wannabe_owner: LocalAccount
) -> None:
    if owner.address == wannabe_owner.address:
        return
    setup_project(owner)
    with reverts("GasMonetization: project already registered"):
        gas_monetization.setProjectContracts(wannabe_owner, ProjectParams.contracts[0:2], {'from': projects_manager})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_project_metadata_uri_can_be_updated(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    setup_project(owner)
    tx: TransactionReceipt = gas_monetization.updateProjectMetadataUri(owner, 'new-uri', {'from': projects_manager})
    assert tx.events['ProjectMetadataUriUpdated'] is not None
    assert tx.events['ProjectMetadataUriUpdated']['owner'] == owner
    assert tx.events['ProjectMetadataUriUpdated']['metadataUri'] == 'new-uri'
    assert gas_monetization.getProjectMetadataUri(owner) == 'new-uri'


@given(
    owner=strategy('address'),
    non_projects_manager=strategy('address')
)
@settings(max_examples=10)
def test_non_project_manager_cannot_update_project_metadata_uri(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        non_projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    if projects_manager.address == non_projects_manager.address:
        return
    setup_project(owner)
    with reverts("GasMonetization: not projects manager"):
        gas_monetization.updateProjectMetadataUri(owner, 'new-uri', {'from': non_projects_manager})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_cannot_update_project_metadata_uri_when_project_does_not_exist(
        gas_monetization: ProjectContract,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    with reverts("GasMonetization: project does not exist"):
        gas_monetization.updateProjectMetadataUri(owner, 'new-uri', {'from': projects_manager})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_cannot_update_project_metadata_uri_when_is_empty(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        projects_manager: LocalAccount,
        owner: LocalAccount
) -> None:
    setup_project(owner)
    with reverts("GasMonetization: empty metadata uri"):
        gas_monetization.updateProjectMetadataUri(owner, '', {'from': projects_manager})
