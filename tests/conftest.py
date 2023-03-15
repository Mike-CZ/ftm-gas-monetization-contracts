import pytest
from brownie import Wei, accounts, GasMonetizationMock, SfcMock
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from utils.constants import WITHDRAWAL_EPOCHS_LIMIT, WITHDRAWAL_CONFIRMATION, ProjectParams
from typing import Callable


@pytest.fixture(scope="session")
def admin() -> LocalAccount:
    return accounts[0]


@pytest.fixture(scope="session")
def funder() -> LocalAccount:
    return accounts[1]


@pytest.fixture(scope="session")
def funds_manager() -> LocalAccount:
    return accounts[2]


@pytest.fixture(scope="session")
def projects_manager() -> LocalAccount:
    return accounts[3]


@pytest.fixture(scope="session")
def data_provider_1() -> LocalAccount:
    return accounts[4]


@pytest.fixture(scope="session")
def data_provider_2() -> LocalAccount:
    return accounts[5]


@pytest.fixture(scope="session")
def data_provider_3() -> LocalAccount:
    return accounts[6]


@pytest.fixture(scope="session")
def data_provider_4() -> LocalAccount:
    return accounts[7]


@pytest.fixture(scope="session")
def data_provider_5() -> LocalAccount:
    return accounts[8]


@pytest.fixture(scope="session")
def data_providers(
        data_provider_1: LocalAccount,
        data_provider_2: LocalAccount,
        data_provider_3: LocalAccount,
        data_provider_4: LocalAccount,
        data_provider_5: LocalAccount,
) -> list[LocalAccount]:
    return [data_provider_1, data_provider_2, data_provider_3, data_provider_4, data_provider_5]


@pytest.fixture(scope="module")
def sfc(admin: LocalAccount) -> ProjectContract:
    return SfcMock.deploy({'from': admin})


@pytest.fixture(scope="module")
def set_epoch_number(admin: LocalAccount, sfc: ProjectContract) -> Callable:
    def set_epoch_number_(number: int) -> None:
        sfc.setEpoch(number, {'from': admin})
    return set_epoch_number_


@pytest.fixture(scope="module")
def gas_monetization(
        admin: LocalAccount,
        sfc: ProjectContract,
        funder: LocalAccount,
        funds_manager: LocalAccount,
        projects_manager: LocalAccount,
        data_providers: list[LocalAccount]
) -> ProjectContract:
    # deploy contract and initialize roles
    contract: ProjectContract = GasMonetizationMock.deploy(
        sfc, WITHDRAWAL_EPOCHS_LIMIT, WITHDRAWAL_CONFIRMATION, {'from': admin}
    )
    contract.grantRole(contract.FUNDER_ROLE(), funder, {'from': admin})
    contract.grantRole(contract.FUNDS_MANAGER_ROLE(), funds_manager, {'from': admin})
    contract.grantRole(contract.PROJECTS_MANAGER_ROLE(), projects_manager, {'from': admin})
    for provider in data_providers:
        contract.grantRole(contract.REWARDS_DATA_PROVIDER_ROLE(), provider, {'from': admin})
    return contract


@pytest.fixture(scope="module")
def setup_gas_monetization_with_funds(
        gas_monetization: ProjectContract,
        funder: LocalAccount,
) -> Callable:
    def setup_gas_monetization_with_funds_(initial_funds: int = Wei("1 ether")) -> None:
        if initial_funds > 0:
            gas_monetization.addFunds({'from': funder, 'amount': initial_funds})
    return setup_gas_monetization_with_funds_


@pytest.fixture(scope='module')
def setup_project(gas_monetization: ProjectContract, projects_manager: LocalAccount) -> Callable:
    def setup_project_(owner: LocalAccount, rewards_recipient: LocalAccount) -> None:
        gas_monetization.addProject(
            owner, rewards_recipient, ProjectParams.metadata_uri, ProjectParams.contracts, {'from': projects_manager}
        )
    return setup_project_

@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation) -> None:
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass

