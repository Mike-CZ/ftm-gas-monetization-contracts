from brownie.test import given, strategy
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from hypothesis import settings

@given(funder=strategy('address'))
@settings(max_examples=10)
def test_funder_can_be_added(
        gas_monetization: ProjectContract,
        owner: LocalAccount,
        funder: LocalAccount
) -> None:
    assert gas_monetization.isFunder(funder) is False
    tx = gas_monetization.addFunder(funder, {'from': owner})
    assert tx.events['FunderAdded'] is not None
    assert tx.events['FunderAdded']['funder'] == funder
    assert gas_monetization.isFunder(funder) is True


@given(funder=strategy('address'))
@settings(max_examples=10)
def test_funder_can_be_removed(
        gas_monetization: ProjectContract,
        owner: LocalAccount,
        funder: LocalAccount
) -> None:
    gas_monetization.addFunder(funder, {'from': owner})
    assert gas_monetization.isFunder(funder) is True
    tx = gas_monetization.removeFunder(funder, {'from': owner})
    assert tx.events['FunderRemoved'] is not None
    assert tx.events['FunderRemoved']['funder'] == funder
    assert gas_monetization.isFunder(funder) is False


@given(funder=strategy('address'))
@settings(max_examples=10)
def test_funds_can_be_added(
        gas_monetization: ProjectContract,
        owner: LocalAccount,
        funder: LocalAccount
) -> None:
    initial_contract_balance = gas_monetization.balance()
    initial_funder_balance = funder.balance()
    gas_monetization.addFunder(funder, {'from': owner})
    tx = gas_monetization.addFunds({'from': funder, 'amount': 1_000})
    assert tx.events['FundsAdded'] is not None
    assert tx.events['FundsAdded']['funder'] == funder
    assert tx.events['FundsAdded']['amount'] == 1_000
    assert gas_monetization.balance() == initial_contract_balance + 1_000
    assert funder.balance() == initial_funder_balance - 1_000
