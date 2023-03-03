from brownie import reverts
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from brownie.network.transaction import TransactionReceipt
from brownie.test import given, strategy
from hypothesis import settings

def test_withdrawal_block_limit_can_be_updated(
        gas_monetization: ProjectContract,
        admin: LocalAccount
) -> None:
    new_limit = 5_000
    tx: TransactionReceipt = gas_monetization.updateWithdrawalBlocksFrequencyLimit(new_limit, {'from': admin})
    assert tx.events['WithdrawalBlockLimitUpdated'] is not None
    assert tx.events['WithdrawalBlockLimitUpdated']['limit'] == new_limit
    assert gas_monetization.getWithdrawalBlocksFrequencyLimit() == new_limit


@given(wannabe_admin=strategy('address'))
@settings(max_examples=10)
def test_non_admin_cannot_update_withdrawal_block_limit(
        gas_monetization: ProjectContract,
        admin: LocalAccount,
        wannabe_admin: LocalAccount
) -> None:
    if wannabe_admin.address == admin.address:
        return
    with reverts('GasMonetization: not admin'):
        gas_monetization.updateWithdrawalBlocksFrequencyLimit(5_000, {'from': wannabe_admin})


def test_withdrawal_confirmation_limit_can_be_updated(
        gas_monetization: ProjectContract,
        admin: LocalAccount
) -> None:
    new_limit = 5
    tx: TransactionReceipt = gas_monetization.updateWithdrawalConfirmationsLimit(new_limit, {'from': admin})
    assert tx.events['WithdrawalConfirmationsLimitUpdated'] is not None
    assert tx.events['WithdrawalConfirmationsLimitUpdated']['limit'] == new_limit
    assert gas_monetization.getWithdrawalConfirmationsLimit() == new_limit


@given(wannabe_admin=strategy('address'))
@settings(max_examples=10)
def test_non_admin_cannot_update_confirmation_limit(
        gas_monetization: ProjectContract,
        admin: LocalAccount,
        wannabe_admin: LocalAccount
) -> None:
    if wannabe_admin.address == admin.address:
        return
    with reverts('GasMonetization: not admin'):
        gas_monetization.updateWithdrawalConfirmationsLimit(5, {'from': wannabe_admin})


def test_withdrawal_deviation_can_be_updated(
        gas_monetization: ProjectContract,
        admin: LocalAccount
) -> None:
    new_limit = 0
    tx: TransactionReceipt = gas_monetization.updateWithdrawalAllowedConfirmationsDeviation(new_limit, {'from': admin})
    assert tx.events['WithdrawalConfirmationsDeviationUpdated'] is not None
    assert tx.events['WithdrawalConfirmationsDeviationUpdated']['limit'] == new_limit
    assert gas_monetization.getWithdrawalAllowedConfirmationsDeviation() == new_limit


@given(wannabe_admin=strategy('address'))
@settings(max_examples=10)
def test_non_admin_cannot_update_deviation(
        gas_monetization: ProjectContract,
        admin: LocalAccount,
        wannabe_admin: LocalAccount
) -> None:
    if wannabe_admin.address == admin.address:
        return
    with reverts('GasMonetization: not admin'):
        gas_monetization.updateWithdrawalAllowedConfirmationsDeviation(0, {'from': wannabe_admin})
