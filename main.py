import ccxt
import config
import pandas

exchange = ccxt.binance({
  'enableRateLimit': True,
  'apiKey': config.BINANCE_KEY,
  'secret': config.BINANCE_SECRET,
})

symbol = 'BTCUSDT'
timeframe = '15m'
limit = 200

# 6 - Create limit order
def limitOrder():
  size = 0.001
  price = 20000

  exchange.create_limit_buy_order(symbol, size, price)

# 5 - Fetch open positions
def fetchOpen():
  positions = exchange.fetch_open_orders(symbol)
  print(positions)

# 4 - Cancel orders
def cancelOrders():
  exchange.cancel_all_orders(symbol)

# 3 - Cancel conditional orders
def cancelConditionalOrders():
  exchange.cancel_all_orders(symbol=symbol, params={'untriggered': True})

# 2 - Get the orderbook
def getOrderbook():
  orderbook = exchange.fetch_order_book(symbol)
  bid = orderbook['bids'][0][0]
  ask = orderbook['asks'][0][0]
  print(f'BID: {bid} ASK: {ask}')

# 1 - Open-High-Low-Close-Volume
def getOhlcv():
  bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
  
  # format the OHLCV to DataFrame
  dataFrame = pandas.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
  dataFrame['timestamp'] = pandas.to_datetime(dataFrame['timestamp'], unit='ms')
  print(dataFrame)

