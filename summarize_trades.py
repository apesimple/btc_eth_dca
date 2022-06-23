import pandas as pd
from dca import load_trades
from slack_functions import send_slack_msg

trades = load_trades()
trades = trades.sort_values('orderid')

last_price = trades[['symbol', 'price']].groupby('symbol')['price'].last()
summary = trades[['symbol', 'size', 'fee', 'cost']].\
    groupby('symbol').agg(total_cost=('cost', sum), total_fee=('fee', sum), total_size=('size', sum)).reset_index()

summary['avg_price'] = round((summary['total_cost'] + summary['total_fee']) / summary['total_size'], 2)

summary = pd.merge(summary, last_price, on='symbol')

print(summary)

send_slack_msg(f"```{summary[['symbol', 'total_size', 'avg_price']].to_string()}```")