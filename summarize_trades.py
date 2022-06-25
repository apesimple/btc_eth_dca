from helper_functions import send_slack_msg, connect_to_ftx, load_trades

TRADES_FILENAME = 'FTX_TRADE_HISTORY.csv'

FTX = connect_to_ftx()
trades = load_trades(TRADES_FILENAME)
trades = trades.sort_values('orderid')

balances = FTX.fetch_balance()
summary = trades[['symbol', 'size', 'fee', 'cost']].\
    groupby('symbol').agg(total_cost=('cost', sum), total_fee=('fee', sum), total_size=('size', sum)).reset_index()

summary['total_invested'] = summary['total_cost'] + summary['total_fee']
summary['avg_price'] = round(summary['total_invested'] / summary['total_size'], 2)

for idx, item in summary.iterrows():
    ticker = FTX.fetch_ticker(item['symbol'])
    summary.loc[summary['symbol'] == item['symbol'], 'last_price'] = ticker['last']

summary['current_value'] = summary['total_size'] * summary['last_price']
print(summary)
text = \
f"""
USD Balance: {round(balances['total']['USD']):,}
Total Invested: {round(summary['total_invested'].sum()):,}
  BTC: {round(summary.loc[summary['symbol'] == 'BTC/USD', 'total_invested'].iloc[0]):,}
  ETH: {round(summary.loc[summary['symbol'] == 'ETH/USD', 'total_invested'].iloc[0]):,}
  Trades: {trades['orderid'].nunique() / 2}
Current Value: {round(summary['current_value'].sum()):,}
  BTC: {round(summary.loc[summary['symbol'] == 'BTC/USD', 'current_value'].iloc[0]):,}
  ETH: {round(summary.loc[summary['symbol'] == 'ETH/USD', 'current_value'].iloc[0]):,}
BTC Balance: {round(summary.loc[summary['symbol'] == 'BTC/USD', 'total_size'].iloc[0], 4)}
  Current Price: ${round(summary.loc[summary['symbol'] == 'BTC/USD', 'last_price'].iloc[0]):,}
  Average Price: ${round(summary.loc[summary['symbol'] == 'BTC/USD', 'avg_price'].iloc[0]):,}
ETH Balance: {round(summary.loc[summary['symbol'] == 'ETH/USD', 'total_size'].iloc[0], 4)}
  Current Price: ${round(summary.loc[summary['symbol'] == 'ETH/USD', 'last_price'].iloc[0]):,}
  Average Price: ${round(summary.loc[summary['symbol'] == 'ETH/USD', 'avg_price'].iloc[0]):,}
"""

send_slack_msg(f"```{text}```", "#dca")

FTX.fetch_markets()