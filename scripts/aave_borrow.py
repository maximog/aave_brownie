from scripts.helpful_scripts import get_account
from brownie import network, config, interface
from scripts.get_weth import get_weth, unwrap
from web3 import Web3

AMOUNT = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork", "kovan"]:
        get_weth()
    lending_pool = get_lending_pool()
    print(f"Lending pool address: {lending_pool}")
    approve_erc20(AMOUNT, lending_pool.address, erc20_address, account)
    print("Depositing...")
    deposit_tx = lending_pool.deposit(
        erc20_address,
        AMOUNT,
        account.address,
        0,
        {"from": account},
    )
    deposit_tx.wait(1)
    print("Deposited!!")
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    print("Let's borrow DAI:")
    # DAI in terms of ETH
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    amount_of_dai_to_borrow = (1 / dai_eth_price) * borrowable_eth * 0.95
    print(f"We are going to borrow {amount_of_dai_to_borrow} DAI")
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(amount_of_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("We borrowed some DAI")
    get_borrowable_data(lending_pool, account)
    repay_all(amount_of_dai_to_borrow, lending_pool, dai_address, account)
    print("You just deposited, borrowed, and repayed")
    get_borrowable_data(lending_pool, account)
    print("Withdrawing deposited WETH...")
    withdraw_tx = lending_pool.withdraw(
        erc20_address, AMOUNT * 0.9999999, account, {"from": account}
    )
    withdraw_tx.wait(1)
    print("Withdrew WETH")
    get_borrowable_data(lending_pool, account)
    print("Converting WETH...")
    unwrap_tx = unwrap(AMOUNT * 0.9999999)
    unwrap_tx.wait(1)
    print("Unwrapped WETH to ETH")
    print(f"Total balance: {Web3.fromWei(account.balance(), 'ether')} ETH")


def repay_all(amount, lending_pool, token_address, account):
    print(f"Repaying: {amount} DAI")
    converted_amount = Web3.toWei(amount, "ether")
    approve_erc20(converted_amount, lending_pool, token_address, account)
    repay_tx = lending_pool.repay(
        token_address, converted_amount, 1, account.address, {"from": account}
    )
    repay_tx.wait(1)
    print("Repayed!!")


def get_asset_price(price_feed_address):
    # ABI and ADDRESS
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"Latest DAI/ETH: {converted_latest_price}")
    return float(converted_latest_price)


def get_borrowable_data(lending_pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    print("----------")
    print(f"{total_collateral_eth} ETH deposited")
    print(f"{total_debt_eth} ETH borrowed")
    print(f"You can borrow {available_borrow_eth} ETH")
    print("----------")
    return (float(available_borrow_eth), float(total_debt_eth))


def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20 token...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved!")
    return tx


def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
