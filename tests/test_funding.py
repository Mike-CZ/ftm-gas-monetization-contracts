from brownie import reverts
from brownie.network.transaction import TransactionReceipt
from brownie.test import given, strategy
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from hypothesis import settings
from typing import Callable


def test_contract_can_be_funded(
        gas_monetization: ProjectContract,
        funder: LocalAccount
) -> None:
    initial_contract_balance = gas_monetization.balance()
    initial_funder_balance = funder.balance()
    tx: TransactionReceipt = gas_monetization.addFunds({'from': funder, 'amount': 1_000})
    assert tx.events['FundsAdded'] is not None
    assert tx.events['FundsAdded']['funder'] == funder
    assert tx.events['FundsAdded']['amount'] == 1_000
    assert gas_monetization.balance() == initial_contract_balance + 1_000
    assert funder.balance() == initial_funder_balance - 1_000


def test_last_epoch_funded_is_updated_on_funding(
        gas_monetization: ProjectContract,
        setup_gas_monetization_with_funds: Callable,
        set_epoch_number: Callable,
        funder: LocalAccount
) -> None:
    epoch = 20
    setup_gas_monetization_with_funds(epoch=epoch)
    gas_monetization.getLastEpochFundsAdded()
    assert gas_monetization.getLastEpochFundsAdded() == epoch
    epoch += 40
    set_epoch_number(epoch)
    gas_monetization.addFunds({'from': funder, 'amount': 1_000})
    assert gas_monetization.getLastEpochFundsAdded() == epoch


@given(non_funder=strategy('address'))
@settings(max_examples=10)
def test_non_funder_cannot_fund_contract(
        gas_monetization: ProjectContract,
        funder: LocalAccount,
        non_funder: LocalAccount
) -> None:
    if non_funder.address == funder.address:
        return
    with reverts("GasMonetization: not funder"):
        gas_monetization.addFunds({'from': non_funder, 'amount': 1_000})


def test_contract_cannot_be_funded_with_empty_amount(
        gas_monetization: ProjectContract,
        funder: LocalAccount
) -> None:
    with reverts("GasMonetization: no funds sent"):
        gas_monetization.addFunds({'from': funder, 'amount': 0})


def test_contract_can_be_funded_via_transfer(
        gas_monetization: ProjectContract,
        funder: LocalAccount
) -> None:
    initial_contract_balance = gas_monetization.balance()
    initial_funder_balance = funder.balance()
    funder.transfer(gas_monetization, 1_000)
    assert gas_monetization.balance() == initial_contract_balance + 1_000
    assert funder.balance() == initial_funder_balance - 1_000


@given(non_funder=strategy('address'))
@settings(max_examples=10)
def test_non_funder_cannot_fund_contract_via_transfer(
        gas_monetization: ProjectContract,
        funder: LocalAccount,
        non_funder: LocalAccount
) -> None:
    if non_funder.address == funder.address:
        return
    with reverts("GasMonetization: not funder"):
        non_funder.transfer(gas_monetization, 1_000)


@given(recipient=strategy('address'))
@settings(max_examples=10)
def test_funds_can_be_withdrawn(
        gas_monetization: ProjectContract,
        setup_gas_monetization_with_funds: Callable,
        funds_manager: LocalAccount,
        recipient: LocalAccount
) -> None:
    setup_gas_monetization_with_funds()
    initial_contract_balance = gas_monetization.balance()
    initial_recipient_balance = recipient.balance()
    tx: TransactionReceipt = gas_monetization.withdrawFunds(recipient, 1_000, {'from': funds_manager})
    assert tx.events['FundsWithdrawn'] is not None
    assert tx.events['FundsWithdrawn']['recipient'] == recipient
    assert tx.events['FundsWithdrawn']['amount'] == 1_000
    assert gas_monetization.balance() == initial_contract_balance - 1_000
    assert recipient.balance() == initial_recipient_balance + 1_000


@given(non_funds_manager=strategy('address'))
@settings(max_examples=10)
def test_non_fund_manager_cannot_withdraw(
        gas_monetization: ProjectContract,
        funds_manager: LocalAccount,
        non_funds_manager: LocalAccount
) -> None:
    if non_funds_manager.address == funds_manager.address:
        return
    with reverts("GasMonetization: not funds manager"):
        gas_monetization.withdrawFunds(non_funds_manager, 1_000, {'from': non_funds_manager})


@given(recipient=strategy('address'))
@settings(max_examples=10)
def test_more_funds_than_balance_cannot_be_withdrawn(
        gas_monetization: ProjectContract,
        funds_manager: LocalAccount,
        recipient: LocalAccount
) -> None:
    with reverts("Address: insufficient balance"):
        gas_monetization.withdrawFunds(recipient, gas_monetization.balance() + 1, {'from': funds_manager})


@given(recipient=strategy('address'))
@settings(max_examples=10)
def test_all_funds_can_be_withdrawn(
        gas_monetization: ProjectContract,
        setup_gas_monetization_with_funds: Callable,
        funds_manager: LocalAccount,
        recipient: LocalAccount
) -> None:
    setup_gas_monetization_with_funds()
    initial_contract_balance = gas_monetization.balance()
    initial_recipient_balance = recipient.balance()
    tx: TransactionReceipt = gas_monetization.withdrawAllFunds(recipient, {'from': funds_manager})
    assert tx.events['FundsWithdrawn'] is not None
    assert tx.events['FundsWithdrawn']['recipient'] == recipient
    assert tx.events['FundsWithdrawn']['amount'] == initial_contract_balance
    assert gas_monetization.balance() == 0
    assert recipient.balance() == initial_recipient_balance + initial_contract_balance


@given(non_funds_manager=strategy('address'))
@settings(max_examples=10)
def test_non_fund_manager_cannot_withdraw_all_funds(
        gas_monetization: ProjectContract,
        funds_manager: LocalAccount,
        non_funds_manager: LocalAccount
) -> None:
    if non_funds_manager.address == funds_manager.address:
        return
    with reverts("GasMonetization: not funds manager"):
        gas_monetization.withdrawAllFunds(non_funds_manager, {'from': non_funds_manager})
