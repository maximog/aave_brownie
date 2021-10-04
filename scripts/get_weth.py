from scripts.helpful_scripts import get_account
from brownie import interface, config, network
from web3 import Web3


def main():
    get_weth()


def get_weth():
    # ABI
    # Address
    account = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.deposit({"from": account, "value": Web3.toWei(0.1, "ether")})
    tx.wait(1)
    print("Received 0.1 WETH")
    return tx


def unwrap(value):
    # ABI
    # Address
    account = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    tx = weth.withdraw(value, {"from": account})
    tx.wait(1)
    print(f"Unwrapped {Web3.fromWei(value, 'ether')} ETH")
    return tx
