import pytest
from brownie import reverts
from brownie.network.transaction import TransactionReceipt
from brownie.test import given, strategy
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from hypothesis import settings
from typing import Callable
from utils.constants import WITHDRAWAL_EPOCHS_LIMIT, WITHDRAWAL_CONFIRMATION, ProjectParams


@pytest.fixture(scope='module')
def setup_project_with_withdrawal_request(
        gas_monetization: ProjectContract,
        setup_gas_monetization_with_funds: Callable,
        setup_project: Callable
) -> Callable:
    def setup_project_with_withdrawal_request_(
            owner: LocalAccount,
            rewards_recipient: LocalAccount,
            epoch: int = 200
    ) -> None:
        setup_gas_monetization_with_funds(epoch=epoch)
        setup_project(owner, rewards_recipient)
        gas_monetization.requestWithdrawal(ProjectParams.project_id, {'from': owner})
    return setup_project_with_withdrawal_request_


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_withdrawal_request_can_be_created(
        gas_monetization: ProjectContract,
        setup_gas_monetization_with_funds: Callable,
        setup_project: Callable,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    setup_gas_monetization_with_funds(epoch=250)
    setup_project(owner, rewards_recipient)
    tx: TransactionReceipt = gas_monetization.requestWithdrawal(ProjectParams.project_id, {'from': owner})
    assert tx.events['WithdrawalRequested'] is not None
    assert tx.events['WithdrawalRequested']['projectId'] == ProjectParams.project_id
    assert tx.events['WithdrawalRequested']['requestEpochNumber'] == 250
    assert gas_monetization.hasPendingWithdrawal(ProjectParams.project_id, 250) is True


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
    wannabe_owner=strategy('address')
)
@settings(max_examples=10)
def test_non_owner_cannot_request_withdrawal(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        wannabe_owner: LocalAccount
) -> None:
    if owner.address == wannabe_owner.address:
        return
    setup_project(owner, rewards_recipient)
    with reverts("GasMonetization: not owner"):
        gas_monetization.requestWithdrawal(ProjectParams.project_id, {'from': wannabe_owner})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
)
@settings(max_examples=10)
def test_withdrawal_request_cannot_be_made_when_project_is_disabled(
        gas_monetization: ProjectContract,
        setup_project_with_withdrawal_request: Callable,
        set_epoch_number: Callable,
        owner: LocalAccount,
        projects_manager: LocalAccount,
        rewards_recipient: LocalAccount,
        data_providers: list[LocalAccount]
) -> None:
    setup_project_with_withdrawal_request(owner=owner, rewards_recipient=rewards_recipient, epoch=200)
    # suspend project
    gas_monetization.suspendProject(ProjectParams.project_id, {'from': projects_manager})
    # make withdrawal for eligible epochs
    for provider in data_providers[:WITHDRAWAL_CONFIRMATION]:
        gas_monetization.completeWithdrawal(ProjectParams.project_id, 200, 500, {'from': provider})
    # shift epochs
    set_epoch_number(250)
    with reverts('GasMonetization: project disabled'):
        gas_monetization.requestWithdrawal(ProjectParams.project_id, {'from': owner})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_withdrawal_request_cannot_be_created_when_contract_not_funded(
        gas_monetization: ProjectContract,
        setup_project: Callable,
        owner: LocalAccount,
        rewards_recipient: LocalAccount
) -> None:
    setup_project(owner, rewards_recipient)
    with reverts("GasMonetization: must wait to withdraw"):
        gas_monetization.requestWithdrawal(ProjectParams.project_id, {'from': owner})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_withdrawal_request_cannot_be_created_until_funds_are_added_since_last_withdrawal(
        gas_monetization: ProjectContract,
        setup_project_with_withdrawal_request: Callable,
        set_epoch_number: Callable,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        funder: LocalAccount,
        data_providers: list[LocalAccount]
) -> None:
    epoch = 200
    setup_project_with_withdrawal_request(owner=owner, rewards_recipient=rewards_recipient, epoch=epoch)
    for provider in data_providers[:WITHDRAWAL_CONFIRMATION]:
        gas_monetization.completeWithdrawal(ProjectParams.project_id, 200, 500, {'from': provider})
    # forwards epochs so the withdrawal is available
    epoch += 200 + WITHDRAWAL_EPOCHS_LIMIT + 10
    set_epoch_number(epoch)
    with reverts("GasMonetization: must wait to withdraw"):
        gas_monetization.requestWithdrawal(ProjectParams.project_id, {'from': owner})
    # fund contract and assure withdrawal is now available
    gas_monetization.addFunds({'from': funder, 'amount': 500})
    gas_monetization.requestWithdrawal(ProjectParams.project_id, {'from': owner})
    assert gas_monetization.hasPendingWithdrawal(ProjectParams.project_id, epoch) is True


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_withdrawal_request_cannot_be_created_until_limit_is_reached(
        gas_monetization: ProjectContract,
        setup_project_with_withdrawal_request: Callable,
        set_epoch_number: Callable,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        data_providers: list[LocalAccount]
) -> None:
    setup_project_with_withdrawal_request(owner=owner, rewards_recipient=rewards_recipient, epoch=200)
    # make withdrawal
    for provider in data_providers[:WITHDRAWAL_CONFIRMATION]:
        gas_monetization.completeWithdrawal(ProjectParams.project_id, 200, 500, {'from': provider})
    # shift epochs by lower number than is withdrawal limit
    set_epoch_number(200 + WITHDRAWAL_EPOCHS_LIMIT - 1)
    with reverts("GasMonetization: must wait to withdraw"):
        gas_monetization.requestWithdrawal(ProjectParams.project_id, {'from': owner})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
)
@settings(max_examples=10)
def test_withdrawal_can_be_completed(
        gas_monetization: ProjectContract,
        setup_project_with_withdrawal_request: Callable,
        set_epoch_number: Callable,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        data_providers: list[LocalAccount]
) -> None:
    amount = 5_000
    setup_project_with_withdrawal_request(owner=owner, rewards_recipient=rewards_recipient, epoch=200)
    initial_rewards_recipient_balance = rewards_recipient.balance()
    initial_contract_balance = gas_monetization.balance()
    set_epoch_number(250)
    # take only needed number of providers defined by withdrawal confirmation limit
    for provider in data_providers[:WITHDRAWAL_CONFIRMATION]:
        tx: TransactionReceipt = gas_monetization.completeWithdrawal(
            ProjectParams.project_id, 200, amount, {'from': provider}
        )
    assert tx.events['WithdrawalCompleted'] is not None
    assert tx.events['WithdrawalCompleted']['projectId'] == ProjectParams.project_id
    assert tx.events['WithdrawalCompleted']['requestEpochNumber'] == 200
    assert tx.events['WithdrawalCompleted']['withdrawalEpochNumber'] == 250
    assert tx.events['WithdrawalCompleted']['amount'] == amount
    assert rewards_recipient.balance() == initial_rewards_recipient_balance + amount
    assert gas_monetization.balance() == initial_contract_balance - amount
    assert gas_monetization.hasPendingWithdrawal(ProjectParams.project_id, 200) is False


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_multiple_withdrawals_can_be_completed(
        gas_monetization: ProjectContract,
        setup_gas_monetization_with_funds: Callable,
        setup_project: Callable,
        set_epoch_number: Callable,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        funder: LocalAccount,
        data_providers: list[LocalAccount]
) -> None:
    epoch = 200
    setup_gas_monetization_with_funds(epoch=epoch)
    setup_project(owner=owner, rewards_recipient=rewards_recipient)
    # try to make 4 withdrawals in a row
    for amount in [5_000, 10_000, 15_000, 20_000]:
        rewards_recipient_balance = rewards_recipient.balance()
        contract_balance = gas_monetization.balance()
        tx: TransactionReceipt = gas_monetization.requestWithdrawal(ProjectParams.project_id, {'from': owner})
        for provider in data_providers[:WITHDRAWAL_CONFIRMATION]:
            tx: TransactionReceipt = gas_monetization.completeWithdrawal(
                ProjectParams.project_id, epoch, amount, {'from': provider}
            )
        assert tx.events['WithdrawalCompleted'] is not None
        assert rewards_recipient.balance() == rewards_recipient_balance + amount
        assert gas_monetization.balance() == contract_balance - amount
        assert gas_monetization.hasPendingWithdrawal(ProjectParams.project_id, epoch) is False
        # forwards epochs and fund contract to fulfill conditions
        epoch += WITHDRAWAL_EPOCHS_LIMIT + 1
        set_epoch_number(epoch)
        gas_monetization.addFunds({'from': funder, 'amount': 10_000})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
    wannabe_provider=strategy('address')
)
@settings(max_examples=10)
def test_non_provider_cannot_complete_withdrawal(
        gas_monetization: ProjectContract,
        setup_project_with_withdrawal_request: Callable,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        wannabe_provider: LocalAccount,
        data_providers: list[LocalAccount]
) -> None:
    if wannabe_provider in data_providers:
        return
    block_id = setup_project_with_withdrawal_request(owner=owner, rewards_recipient=rewards_recipient, epoch=200)
    with reverts("GasMonetization: not rewards data provider"):
        gas_monetization.completeWithdrawal(ProjectParams.project_id, block_id, 5_000, {'from': wannabe_provider})


def test_cannot_complete_withdrawal_when_does_not_exist(
        gas_monetization: ProjectContract,
        data_provider_1: LocalAccount
) -> None:
    with reverts("GasMonetization: no withdrawal request"):
        gas_monetization.completeWithdrawal(ProjectParams.project_id, 1, 5_000, {'from': data_provider_1})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_provider_cannot_complete_withdrawal_multiple_times(
        gas_monetization: ProjectContract,
        setup_project_with_withdrawal_request: Callable,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        data_provider_1: LocalAccount
) -> None:
    amount = 5_000
    setup_project_with_withdrawal_request(owner=owner, rewards_recipient=rewards_recipient, epoch=200)
    gas_monetization.completeWithdrawal(ProjectParams.project_id, 200, amount, {'from': data_provider_1})
    with reverts("GasMonetization: already provided"):
        gas_monetization.completeWithdrawal(ProjectParams.project_id, 200, amount, {'from': data_provider_1})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address')
)
@settings(max_examples=10)
def test_provider_cannot_complete_withdrawal_with_empty_amount(
        gas_monetization: ProjectContract,
        setup_project_with_withdrawal_request: Callable,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        data_provider_1: LocalAccount
) -> None:
    setup_project_with_withdrawal_request(owner=owner, rewards_recipient=rewards_recipient, epoch=200)
    with reverts("GasMonetization: no amount to withdraw"):
        gas_monetization.completeWithdrawal(ProjectParams.project_id, 200, 0, {'from': data_provider_1})


@given(
    owner=strategy('address'),
    rewards_recipient=strategy('address'),
)
@settings(max_examples=10)
def test_withdrawal_is_reset_on_incorrect_confirmation(
        gas_monetization: ProjectContract,
        setup_project_with_withdrawal_request: Callable,
        owner: LocalAccount,
        rewards_recipient: LocalAccount,
        data_providers: list[LocalAccount]
) -> None:
    setup_project_with_withdrawal_request(owner=owner, rewards_recipient=rewards_recipient, epoch=200)
    gas_monetization.completeWithdrawal(ProjectParams.project_id, 200, 500, {'from': data_providers[0]})
    tx: TransactionReceipt = gas_monetization.completeWithdrawal(
        ProjectParams.project_id, 200, 1000, {'from': data_providers[1]}
    )
    assert tx.events['InvalidWithdrawalAmount'] is not None
    assert tx.events['InvalidWithdrawalAmount']['projectId'] == ProjectParams.project_id
    assert tx.events['InvalidWithdrawalAmount']['withdrawalEpochNumber'] == 200
    assert tx.events['InvalidWithdrawalAmount']['amount'] == 500
    assert tx.events['InvalidWithdrawalAmount']['diffAmount'] == 1000
    assert gas_monetization.getPendingRequestConfirmationsEpochId(ProjectParams.project_id) == 200
    assert gas_monetization.getPendingRequestConfirmationsCount(ProjectParams.project_id) == 0
    assert gas_monetization.getPendingRequestConfirmationsValue(ProjectParams.project_id) == 0
    assert len(gas_monetization.getPendingRequestConfirmationsProviders(ProjectParams.project_id)) == 0
