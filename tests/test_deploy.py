from brownie import reverts, GasMonetizationMock
from brownie.test import given, strategy
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from hypothesis import settings

@given(
    owner=strategy('address'),
    sfc=strategy('address')
)
@settings(max_examples=10)
def test_contract_can_be_deployed(
        owner: LocalAccount,
        sfc: LocalAccount
) -> None:
    epochs_limit = 10
    withdrawal_limit = 5
    contract: ProjectContract = GasMonetizationMock.deploy(sfc, epochs_limit, withdrawal_limit, {'from': owner})
    assert contract.tx.events['ContractDeployed'] is not None
    assert contract.tx.events['ContractDeployed']['sfcAddress'] == sfc
    assert contract.tx.events['ContractDeployed']['withdrawalEpochsFrequencyLimit'] == epochs_limit
    assert contract.tx.events['ContractDeployed']['confirmationsToMakeWithdrawal'] == withdrawal_limit
    assert contract.getWithdrawalEpochsFrequencyLimit() == epochs_limit
    assert contract.getWithdrawalConfirmationsLimit() == withdrawal_limit
    assert contract.getSfcAddress() == sfc
