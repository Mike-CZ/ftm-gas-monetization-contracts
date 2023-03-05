import pytest
from brownie import reverts, chain
from brownie.network.transaction import TransactionReceipt
from brownie.test import given, strategy
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from hypothesis import settings
from typing import Callable
from utils.constants import WITHDRAWAL_BLOCKS_LIMIT, WITHDRAWAL_CONFIRMATION


@pytest.fixture(scope='module')
def setup_withdrawal_request(
        gas_monetization: ProjectContract,
        setup_gas_monetization_with_funds: Callable,
        setup_project: Callable
) -> Callable:
    def setup_withdrawal_request_(owner: LocalAccount) -> int:
        setup_gas_monetization_with_funds()
        setup_project(owner)
        tx: TransactionReceipt = gas_monetization.requestWithdrawal({'from': owner})
        return tx.block_number

    return setup_withdrawal_request_


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_withdrawal_request_can_be_created(
        gas_monetization: ProjectContract,
        setup_gas_monetization_with_funds: Callable,
        setup_project: Callable,
        owner: LocalAccount
) -> None:
    setup_gas_monetization_with_funds()
    setup_project(owner)
    tx: TransactionReceipt = gas_monetization.requestWithdrawal({'from': owner})
    assert tx.events['WithdrawalRequested'] is not None
    assert tx.events['WithdrawalRequested']['owner'] == owner
    assert tx.events['WithdrawalRequested']['blockNumber'] == tx.block_number
    assert gas_monetization.hasPendingWithdrawal(owner, tx.block_number) is True


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_withdrawal_request_cancels_previously_pending(
        gas_monetization: ProjectContract,
        setup_gas_monetization_with_funds: Callable,
        setup_project: Callable,
        owner: LocalAccount
) -> None:
    setup_gas_monetization_with_funds()
    setup_project(owner)
    tx: TransactionReceipt = gas_monetization.requestWithdrawal({'from': owner})
    assert gas_monetization.hasPendingWithdrawal(owner, tx.block_number) is True
    # obtain block id of previous withdrawal and mine new blocks to get ahead of blocks limit
    previous_block_id = tx.block_number
    chain.mine(WITHDRAWAL_BLOCKS_LIMIT)
    tx: TransactionReceipt = gas_monetization.requestWithdrawal({'from': owner})
    # assert previous request is canceled
    assert tx.events['WithdrawalCanceled'] is not None
    assert tx.events['WithdrawalCanceled']['owner'] == owner
    assert tx.events['WithdrawalCanceled']['blockNumber'] == previous_block_id
    assert gas_monetization.hasPendingWithdrawal(owner, previous_block_id) is False
    # assert new request is pending
    assert gas_monetization.hasPendingWithdrawal(owner, tx.block_number) is True


@given(
    owner=strategy('address'),
    wannabe_owner=strategy('address')
)
@settings(max_examples=10)
def test_non_owner_cannot_request_withdrawal(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        owner: LocalAccount,
        wannabe_owner: LocalAccount
) -> None:
    if owner.address == wannabe_owner.address:
        return
    setup_project(owner)
    with reverts("GasMonetization: not project owner"):
        gas_monetization.requestWithdrawal({'from': wannabe_owner})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_withdrawal_request_cannot_be_created_when_contract_not_funded(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        owner: LocalAccount
) -> None:
    setup_project(owner)
    with reverts("GasMonetization: must wait to withdraw"):
        gas_monetization.requestWithdrawal({'from': owner})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_withdrawal_request_cannot_be_created_until_limit_is_reached(
        gas_monetization: ProjectContract,
        setup_gas_monetization_with_funds: Callable,
        setup_project: Callable,
        owner: LocalAccount
) -> None:
    setup_gas_monetization_with_funds()
    setup_project(owner)
    gas_monetization.requestWithdrawal({'from': owner})
    with reverts("GasMonetization: must wait to withdraw"):
        gas_monetization.requestWithdrawal({'from': owner})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_withdrawal_request_cannot_be_created_until_last_withdrawal_limit_is_reached(
        gas_monetization: ProjectContract,
        setup_gas_monetization_with_funds: Callable,
        setup_project: Callable,
        owner: LocalAccount,
        data_providers: list[LocalAccount]
) -> None:
    setup_gas_monetization_with_funds()
    setup_project(owner)
    tx = gas_monetization.requestWithdrawal({'from': owner})
    block_id = tx.block_number
    # mine new blocks to make sure withdrawal is not declined because pending withdrawal limit
    chain.mine(WITHDRAWAL_BLOCKS_LIMIT + 1)
    # make withdrawal
    for provider in data_providers[:WITHDRAWAL_CONFIRMATION]:
        gas_monetization.completeWithdrawal(owner, block_id, 500, {'from': provider})
    with reverts("GasMonetization: must wait to withdraw"):
        gas_monetization.requestWithdrawal({'from': owner})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_withdrawal_request_cannot_be_created_until_funds_are_added_since_last_withdrawal(
        gas_monetization: ProjectContract,
        setup_gas_monetization_with_funds: Callable,
        setup_project: Callable,
        owner: LocalAccount,
        funder: LocalAccount,
        data_providers: list[LocalAccount]
) -> None:
    setup_gas_monetization_with_funds()
    setup_project(owner)
    tx = gas_monetization.requestWithdrawal({'from': owner})
    # mine new blocks to make sure withdrawal is not declined because pending withdrawal limit
    chain.mine(WITHDRAWAL_BLOCKS_LIMIT)
    # make withdrawal
    for provider in data_providers[:WITHDRAWAL_CONFIRMATION]:
        gas_monetization.completeWithdrawal(owner, tx.block_number, 500, {'from': provider})
    # mine new blocks so the withdrawal is available
    chain.mine(WITHDRAWAL_BLOCKS_LIMIT)
    with reverts("GasMonetization: must wait to withdraw"):
        gas_monetization.requestWithdrawal({'from': owner})
    # fund contract and assure withdrawal is now available
    gas_monetization.addFunds({'from': funder, 'amount': 500})
    tx: TransactionReceipt = gas_monetization.requestWithdrawal({'from': owner})
    assert gas_monetization.hasPendingWithdrawal(owner, tx.block_number) is True


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_withdrawal_can_be_completed(
        gas_monetization: ProjectContract,
        setup_withdrawal_request: Callable,
        owner: LocalAccount,
        data_providers: list[LocalAccount]
) -> None:
    amount = 5_000
    block_id = setup_withdrawal_request(owner)
    initial_owner_balance = owner.balance()
    initial_contract_balance = gas_monetization.balance()
    # take only needed number of providers defined by withdrawal confirmation limit
    for provider in data_providers[:WITHDRAWAL_CONFIRMATION]:
        tx: TransactionReceipt = gas_monetization.completeWithdrawal(owner, block_id, amount, {'from': provider})
    assert tx.events['WithdrawalCompleted'] is not None
    assert tx.events['WithdrawalCompleted']['owner'] == owner
    assert tx.events['WithdrawalCompleted']['blockNumber'] == block_id
    assert tx.events['WithdrawalCompleted']['amount'] == amount
    assert owner.balance() == initial_owner_balance + amount
    assert gas_monetization.balance() == initial_contract_balance - amount
    assert gas_monetization.hasPendingWithdrawal(owner, block_id) is False


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_multiple_withdrawals_can_be_completed(
        gas_monetization: ProjectContract,
        setup_gas_monetization_with_funds: Callable,
        setup_project: Callable,
        owner: LocalAccount,
        funder: LocalAccount,
        data_providers: list[LocalAccount]
) -> None:
    setup_gas_monetization_with_funds()
    setup_project(owner)
    # try to make 4 withdrawals in a row
    for amount in [5_000, 10_000, 15_000, 20_000]:
        owner_balance = owner.balance()
        contract_balance = gas_monetization.balance()
        tx: TransactionReceipt = gas_monetization.requestWithdrawal({'from': owner})
        block_id = tx.block_number
        for provider in data_providers[:WITHDRAWAL_CONFIRMATION]:
            tx: TransactionReceipt = gas_monetization.completeWithdrawal(owner, block_id, amount, {'from': provider})
        assert tx.events['WithdrawalCompleted'] is not None
        assert owner.balance() == owner_balance + amount
        assert gas_monetization.balance() == contract_balance - amount
        assert gas_monetization.hasPendingWithdrawal(owner, block_id) is False
        # mine new blocks and fund contract to fulfill conditions
        chain.mine(WITHDRAWAL_BLOCKS_LIMIT)
        gas_monetization.addFunds({'from': funder, 'amount': 10_000})


@given(
    owner=strategy('address'),
    wannabe_provider=strategy('address')
)
@settings(max_examples=10)
def test_non_provider_cannot_complete_withdrawal(
        gas_monetization: ProjectContract,
        setup_withdrawal_request: Callable,
        owner: LocalAccount,
        wannabe_provider: LocalAccount,
        data_providers: list[LocalAccount]
) -> None:
    if wannabe_provider in data_providers:
        return
    block_id = setup_withdrawal_request(owner)
    with reverts("GasMonetization: not rewards data provider"):
        gas_monetization.completeWithdrawal(owner, block_id, 5_000, {'from': wannabe_provider})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_cannot_complete_withdrawal_when_does_not_exist(
        gas_monetization: ProjectContract,
        owner: LocalAccount,
        data_provider_1: LocalAccount
) -> None:
    with reverts("GasMonetization: no withdrawal request"):
        gas_monetization.completeWithdrawal(owner, 1, 5_000, {'from': data_provider_1})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_provider_cannot_complete_withdrawal_multiple_times(
        gas_monetization: ProjectContract,
        setup_withdrawal_request: Callable,
        owner: LocalAccount,
        data_provider_1: LocalAccount
) -> None:
    amount = 5_000
    block_id = setup_withdrawal_request(owner)
    gas_monetization.completeWithdrawal(owner, block_id, amount, {'from': data_provider_1})
    with reverts("GasMonetization: already confirmed"):
        gas_monetization.completeWithdrawal(owner, block_id, amount, {'from': data_provider_1})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_provider_cannot_complete_withdrawal_with_empty_amount(
        gas_monetization: ProjectContract,
        setup_withdrawal_request: Callable,
        owner: LocalAccount,
        data_provider_1: LocalAccount
) -> None:
    block_id = setup_withdrawal_request(owner)
    with reverts("GasMonetization: no amount to withdraw"):
        gas_monetization.completeWithdrawal(owner, block_id, 0, {'from': data_provider_1})


@given(owner=strategy('address'))
@settings(max_examples=10)
def test_withdrawal_is_canceled_on_too_many_incorrect_confirmations(
        gas_monetization: ProjectContract,
        setup_withdrawal_request: Callable,
        owner: LocalAccount,
        data_providers: list[LocalAccount]
) -> None:
    block_id = setup_withdrawal_request(owner)
    for index, provider in enumerate(data_providers):
        tx: TransactionReceipt = gas_monetization.completeWithdrawal(
            owner, block_id, index + 500, {'from': provider}
        )
    assert tx.events['WithdrawalCanceled'] is not None
    assert tx.events['WithdrawalCanceled']['owner'] == owner
    assert tx.events['WithdrawalCanceled']['blockNumber'] == block_id
    assert gas_monetization.hasPendingWithdrawal(owner, block_id) is False
