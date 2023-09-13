import asyncio
import sys
import time
import ccxt.pro
from colorama import Style, Fore, init

import utils

init()
print('CCXT Version:', ccxt.pro.__version__)

# bot options
timeout = time.time() + 10
min_profit = 0
min_profit_pct = 0

# exchanges you want to use to look for arbitrage opportunities
exchanges = [
    ccxt.pro.binance(),
    ccxt.pro.bitmart(),
]
exchanges_names = ['binance', 'bitmart']

fees = {
    'binance': {'base': 0, 'quote' : 0.001},
    'bitmart': {'base': 0, 'quote' : 0.0025},
}

# symbols you want to trade
symbols = [
    "SOL/USDT",
]

# order sizes for each symbol, adjust it to your liking
order_sizes = {
    "SOL/USDT": 0.1,
}

total_change_usd = 0
total_change_usd_pct = 0
prec_ask_price = 0
prec_bid_price = 0
opportunity = 0
prec_seconds = '0000000'

funds = 500

bid_prices = {}
ask_prices = {}

usd = {'binance': 250, 'bitmart': 250}
crypto = {'binance': 250, 'bitmart': 250}
order_size = 1

async def symbol_loop(exchange, symbol):
    global opportunity, prec_seconds
    while time.time() <= timeout:
        orderbook = await exchange.watch_order_book(symbol)
        bid_prices['binance'] = orderbook["bids"][0][0]
        ask_prices['binance'] = orderbook["asks"][0][0]
        min_ask_ex = min(ask_prices, key=ask_prices.get)
        max_bid_ex = max(bid_prices, key=bid_prices.get)
        min_ask_price = ask_prices[min_ask_ex]
        max_bid_price = bid_prices[max_bid_ex]

        buy_price = (order_size / (1-fees[min_ask_ex]['quote'])) * min_ask_price * (1+fees[min_ask_ex]['base'])
        sell_price = order_size / (1+fees[max_bid_ex]['base']) * max_bid_price * (1-fees[max_bid_ex]['quote'])
        change_usd = ((usd[min_ask_ex] - buy_price)) + (usd[max_bid_ex] + sell_price) - (usd[min_ask_ex]+usd[max_bid_ex])
        total_usd_balance = 0
        for exc in exchanges_names:
            total_usd_balance+=usd[exc]
        change_usd_pct = (change_usd/total_usd_balance)*100

        if max_bid_ex != min_ask_ex and change_usd > float(min_profit) and change_usd_pct > float(min_profit_pct) and prec_ask_price != min_ask_price and prec_bid_price != max_bid_price:
            opportunity += 1

            fees_crypto = order_size * (1-fees[min_ask_ex]['quote']) + order_size * (1-fees[max_bid_ex]['base'])
            fees_usd = order_size * max_bid_price * (1-fees[max_bid_ex]['quote']) + order_size * min_ask_price * (1-fees[min_ask_ex]['base'])

            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
            print("-----------------------------------------------------\n")

            ex_balances = ""
            for exc in exchanges_names:
              ex_balances+=f"\n➝ {exc}: {round(crypto[exc],3)} {symbol.split('/')[0]} / {round(usd[exc],2)} {symbol.split('/')[1]}"
            print(f"{Style.RESET_ALL}Opportunity n°{opportunity} detected! ({min_ask_ex} {min_ask_price}   ->   {max_bid_price} {max_bid_ex})\n \nExcepted profit: {Fore.GREEN}+{round(change_usd_pct,4)} % (+{round(change_usd,4)} {symbol.split('/')[1]}){Style.RESET_ALL}\n \nSession total profit: {Fore.GREEN}+{round(total_change_usd_pct,4)} %     (+{round((total_change_usd/100)*funds,4)} {symbol.split('/')[1]}){Style.RESET_ALL}\n \nFees paid: {Fore.RED}-{round(fees_usd,4)} {symbol.split('/')[1]}      -{round(fees_crypto,4)} {symbol.split('/')[0]}\n \n{Style.DIM} {ex_balances}\n \n{Style.RESET_ALL}Time elapsed since the beginning of the session: {time.strftime('%H:%M:%S', time.gmtime(time.time()-st))}\n \n{Style.RESET_ALL}-----------------------------------------------------\n \n")

            print(f"{Style.DIM}{utils.get_time()}{Style.RESET_ALL} Sell market order filled on {max_bid_ex} for {order_size} {symbol.split('/')[0]} at {max_bid_price}.")
            print(f"{Style.DIM}{utils.get_time()}{Style.RESET_ALL} Buy market order filled on {max_bid_ex} for {order_size} {symbol.split('/')[0]} at {min_ask_price}.")

            crypto[min_ask_ex] += order_size
            usd[min_ask_ex] -= (order_size / (1-fees[min_ask_ex]['quote'])) * min_ask_price * (1+fees[min_ask_ex]['base'])
            crypto[max_bid_ex] -= order_size
            usd[max_bid_ex] += order_size / (1+fees[max_bid_ex]['base']) * max_bid_price * (1-fees[max_bid_ex]['quote'])

            total_change_usd+=change_usd
            total_change_usd_pct+=change_usd_pct

            prec_ask_price = min_ask_price
            prec_bid_price = max_bid_price
        else:
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
            if change_usd < 0:
              color = Fore.RED
            elif change_usd > 0:
              color = Fore.GREEN
            elif change_usd == 0:
              color = Fore.WHITE
            print(f"{Style.DIM}{utils.get_time()}{Style.RESET_ALL} Best opportunity: {color}{round(change_usd,4)} {symbol.split('/')[1]} {Style.RESET_ALL}(with fees)       buy: {min_ask_ex} at {min_ask_price}     sell: {max_bid_ex} at {max_bid_price}")
            actual_time=exchange.iso8601(exchange.milliseconds())

            # Limit bot to maximum one hour
            if actual_time[17:19] == "00" and actual_time[14:16] != prec_seconds:
                prec_seconds = actual_time[11:13]
                await exchange.close()


async def exchange_loop(exchange, symbols):
    loops = [symbol_loop(exchange, symbol) for symbol in symbols]
    await asyncio.gather(*loops)
    await exchange.close()

async def clear_crypto():
  for exc in exchanges:
      ticker = await exc.fetch_ticker(symbols[0])
      price = ticker['last']
      usd[exc.id]+=((crypto[exc.id])*(1-fees[exc.id]['base'])*price)*(1-fees[exc.id]['quote'])
      crypto[exc.id]=0


async def main():
    loops = [exchange_loop(exchange, symbols) for exchange in exchanges]
    await asyncio.gather(*loops)
    await clear_crypto()
    for exc in exchanges:
       await exc.close()

st = time.time()
print(" \n")
asyncio.get_event_loop().run_until_complete(main())


total_usdt_balance = 0
for exc_name in exchanges_names:
    total_usdt_balance += usd[exc_name]

total_session_profit_usd = total_usdt_balance-funds
total_session_profit_pct = (total_session_profit_usd/funds)*100
print(f"{Style.DIM}{utils.get_time()}{Style.RESET_ALL} Session with {symbols[0].split('/')[0]} finished.")
print(f"{Style.DIM}{utils.get_time()}{Style.RESET_ALL} Total profit: {round(total_session_profit_pct,4)} % ({total_session_profit_usd} {symbols[0].split('/')[1]})")