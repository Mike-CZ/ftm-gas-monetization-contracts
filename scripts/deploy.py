import click
from brownie import GasMonetization
from brownie import network, accounts
from eth_utils import is_address


def validate_eth_address(value):
    if not is_address(value):
        raise click.UsageError("Invalid address!")
    return value


def main():
    click.echo(f"You are using the '{network.show_active()}' network")
    account = accounts.load(click.prompt("Account", type=click.Choice(accounts.load())))
    click.echo(f"You are using account: {account.address}")

    click.echo(f"You are deploying GasMonetization")
    sfc_address = click.prompt('Insert SFC address', value_proc=validate_eth_address)
    epochs_limit = click.prompt('Insert epochs limit to make withdrawal', type=click.IntRange(min=1))
    confirmations = click.prompt('Insert number of confirmations to make withdrawal', type=click.IntRange(min=1))
    publish = click.prompt('Publish source for validation? (API key must be exported)', type=click.BOOL)

    click.echo(
        f"""
        GasMonetization Deployment Parameters
                 sfc address: {sfc_address}
                epochs limit: {epochs_limit}
         confirmations limit: {confirmations}
        """
    )

    if not click.confirm("Deploy GasMonetization"):
        return

    GasMonetization.deploy(sfc_address, epochs_limit, confirmations, {'from': account}, publish_source=publish)

    click.echo("GasMonetization successfully deployed")




