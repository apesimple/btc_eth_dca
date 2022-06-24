import os
import ssl
import ccxt
import configparser
import pandas as pd
from pathlib import Path
from slack import WebClient

script_directory = Path(__file__).resolve().parents[0]
home_path = os.getenv('HOME')
config = configparser.ConfigParser()
config.read(f"{home_path}/config.ini")


def connect_to_ftx():
    FTX = ccxt.ftx({
        'apiKey': config['FTX']['API_KEY'],
        'secret': config['FTX']['SECRET_KEY'],
        'headers': {
            'FTX-SUBACCOUNT': 'DCA',
        }
    })
    return FTX


def load_trades(TRADES_FILENAME):
    try:
        df = pd.read_csv(f"{script_directory}/{TRADES_FILENAME}")
    except FileNotFoundError:
        columns = ['orderid', 'symbol', 'size', 'timestamp',
                   'datetime', 'price', 'tradeid', 'feerate',
                   'fee', 'feecurrency', 'cost']
        df = pd.DataFrame(columns=columns)
    return df


def save_trades(trades, TRADES_FILENAME):
    trades.to_csv(f"{script_directory}/{TRADES_FILENAME}", index=False)


def send_slack_msg(text, channel="#general"):
    home_path = os.getenv('HOME')
    config = configparser.ConfigParser()
    config.read(f"{home_path}/config.ini")
    slack_api_key = config['SLACK']['slack_api_key']

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    slack_client = WebClient(slack_api_key, ssl=ssl_context)
    slack_client.chat_postMessage(channel=channel, text=text)


def slack_link(url, text):
    return f'<{url}|{text}>'