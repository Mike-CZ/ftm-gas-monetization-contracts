from brownie import reverts, GasMonetizationMock
from brownie.test import given, strategy
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from hypothesis import settings

@given(owner=strategy('address'))
@settings(max_examples=10)
def test_contract_can_be_deployed(
        owner: LocalAccount
) -> None:
    blocks_limit = 100
    confirmations = 1
    deviation = 0
    contract: ProjectContract = GasMonetizationMock.deploy(blocks_limit, confirmations, deviation, {'from': owner})
    assert contract.tx.events['ContractDeployed'] is not None
    assert contract.tx.events['ContractDeployed']['withdrawalBlocksFrequencyLimit'] == blocks_limit
    assert contract.tx.events['ContractDeployed']['confirmationsToMakeWithdrawal'] == confirmations
    assert contract.tx.events['ContractDeployed']['allowedConfirmationsDeviation'] == deviation
    assert contract.getWithdrawalBlocksFrequencyLimit() == blocks_limit
    assert contract.getWithdrawalConfirmationsLimit() == confirmations
    assert contract.getWithdrawalAllowedConfirmationsDeviation() == deviation
