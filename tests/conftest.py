import pytest
from brownie import accounts, GasMonetizationMock
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount

@pytest.fixture(scope="session")
def owner() -> LocalAccount:
    return accounts[0]

@pytest.fixture(scope="module")
def gas_monetization(owner: LocalAccount) -> ProjectContract:
    return GasMonetizationMock.deploy({'from': owner})

@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation) -> None:
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass

