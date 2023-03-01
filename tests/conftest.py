import pytest
from brownie import Wei, accounts, GasMonetization
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount

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

@pytest.fixture(scope="module")
def gas_monetization(
        admin: LocalAccount,
        funder: LocalAccount,
        funds_manager: LocalAccount,
        projects_manager: LocalAccount
) -> ProjectContract:
    # deploy contract and initialize roles
    tx = GasMonetization.deploy({'from': admin})
    tx.grantRole(tx.FUNDER_ROLE(), funder, {'from': admin})
    tx.grantRole(tx.FUNDS_MANAGER_ROLE(), funds_manager, {'from': admin})
    tx.grantRole(tx.PROJECTS_MANAGER_ROLE(), projects_manager, {'from': admin})
    # fund contract with initial balance
    tx.addFunds({'from': funder, 'amount': Wei("1 ether")})
    return tx

@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation) -> None:
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass

