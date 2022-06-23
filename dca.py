import os
import configparser
import ccxt
import pandas as pd
import time
from pathlib import Path

home_path = os.getenv('HOME')
script_directory = Path(__file__).resolve().parents[0]
config = configparser.ConfigParser()
config.read(f"{home_path}/config.ini")

FTX = ccxt.ftx({
    'apiKey': config['FTX']['API_KEY'],
    'secret': config['FTX']['SECRET_KEY'],
    'headers': {
        'FTX-SUBACCOUNT': 'DCA',
    }
})

INVESTMENTS = [
    {
        'symbol': 'ETH/USD',
        'dca_amount': 15
    },
    {
        'symbol': 'BTC/USD',
        'dca_amount': 10
    }
]

TRADES_FILENAME = 'FTX_TRADE_HISTORY.csv'


def load_trades():
    try:
        df = pd.read_csv(f"{script_directory}/{TRADES_FILENAME}")
    except FileNotFoundError:
        columns = ['orderid', 'symbol', 'size', 'timestamp',
                   'datetime', 'price', 'tradeid', 'feerate',
                   'fee', 'feecurrency', 'cost']
        df = pd.DataFrame(columns=columns)
    return df


def save_trades(trades):
    trades.to_csv(f"{script_directory}/{TRADES_FILENAME}", index=False)


def market_buy(symbol, size):
    order = FTX.create_order(symbol=symbol, type='market', side='buy', amount=size)
    parsed_order = parse_order(order)
    print(f"{parsed_order['datetime']} Sent order: {parsed_order['orderid']} for {parsed_order['size']} {parsed_order['symbol']}")
    return order


def calculate_base_amount(symbol, quote_amount):
    order_book = FTX.fetch_order_book(symbol)
    best_buy_price = order_book['asks'][0][0]
    base_amount = round(quote_amount / best_buy_price, 6)
    return base_amount


def parse_order(order):
    parsed_order = {
        'orderid': order['id'],
        'symbol': order['symbol'],
        'size': order['amount'],
        'timestamp': order['timestamp'],
        'datetime': order['datetime']
    }
    return parsed_order


def parse_single_trade(trade):
    parsed_trade = {
        'orderid': trade['order'],
        'symbol': trade['symbol'],
        'size': trade['amount'],
        'timestamp': trade['timestamp'],
        'datetime': trade['datetime'],
        'price': trade['price'],
        'tradeid': trade['id'],
        'feerate': float(trade['fee']['rate']),
        'fee': float(trade['fee']['cost']),
        'feecurrency': trade['fee']['currency'],
        'cost': trade['cost']
    }

    return parsed_trade


def parse_trades(trades):
    """ Accepts a list of """
    parsed_trades = []
    for trade in trades:
        parsed_trade = parse_single_trade(trade)
        parsed_trades.append(parsed_trade)

    parsed_trades_df = pd.DataFrame(parsed_trades)
    return parsed_trades_df


def add_trade_records(new_trades):
    """ Parses order and save to file """
    new_parsed_trades = parse_trades(new_trades)

    historical_trades = load_trades()
    trades = pd.concat([historical_trades, new_parsed_trades]).reset_index(drop=True)

    save_trades(trades)


def get_order_trade_info(order):
    order_trade = []
    attempt = 0
    while not order_trade and attempt < 6:
        order_trade = FTX.fetch_order_trades(order['id'])
        if not order_trade:
            time.sleep(2**attempt)
            attempt = attempt + 1

    if not order_trade:
        print(f"Failed to get trades for order: {order}")
    return order_trade


def main():
    for investment in INVESTMENTS:
        symbol = investment['symbol']
        quote_amount = investment['dca_amount']

        size = calculate_base_amount(symbol, quote_amount)
        order = market_buy(symbol, size)
        order_trades = get_order_trade_info(order)
        if order_trades:
            add_trade_records(order_trades)


if __name__ == '__main__':
    main()
