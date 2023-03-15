from brownie import reverts
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from brownie.network.transaction import TransactionReceipt
from brownie.test import given, strategy
from hypothesis import settings

def test_withdrawal_epoch_limit_can_be_updated(
        gas_monetization: ProjectContract,
        admin: LocalAccount
) -> None:
    new_limit = 5_000
    tx: TransactionReceipt = gas_monetization.updateWithdrawalEpochsFrequencyLimit(new_limit, {'from': admin})
    assert tx.events['WithdrawalEpochsLimitUpdated'] is not None
    assert tx.events['WithdrawalEpochsLimitUpdated']['limit'] == new_limit
    assert gas_monetization.getWithdrawalEpochsFrequencyLimit() == new_limit


@given(wannabe_admin=strategy('address'))
@settings(max_examples=10)
def test_non_admin_cannot_update_withdrawal_epoch_limit(
        gas_monetization: ProjectContract,
        admin: LocalAccount,
        wannabe_admin: LocalAccount
) -> None:
    if wannabe_admin.address == admin.address:
        return
    with reverts('GasMonetization: not admin'):
        gas_monetization.updateWithdrawalEpochsFrequencyLimit(5_000, {'from': wannabe_admin})


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


@given(sfc_address=strategy('address'))
@settings(max_examples=10)
def test_sfc_address_can_be_updated(
        gas_monetization: ProjectContract,
        admin: LocalAccount,
        sfc_address: LocalAccount
) -> None:
    tx: TransactionReceipt = gas_monetization.updateSfcAddress(sfc_address, {'from': admin})
    assert tx.events['SfcAddressUpdated'] is not None
    assert tx.events['SfcAddressUpdated']['sfcAddress'] == sfc_address
    assert gas_monetization.getSfcAddress() == sfc_address


@given(
    wannabe_admin=strategy('address'),
    sfc_address=strategy('address')
)
@settings(max_examples=10)
def test_non_admin_cannot_update_sfc_address(
        gas_monetization: ProjectContract,
        admin: LocalAccount,
        wannabe_admin: LocalAccount,
        sfc_address: LocalAccount
) -> None:
    if wannabe_admin.address == admin.address:
        return
    with reverts('GasMonetization: not admin'):
        gas_monetization.updateSfcAddress(sfc_address, {'from': wannabe_admin})
