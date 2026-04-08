import ccxt
import pandas as pd
import time
import requests
import sys

# ==========================================
# 1. SETTINGS
# ==========================================
MY_TOPIC = "OneTrade007" 
COINS = ['DOGE/USDT', 'PIPPIN/USDT', 'POL/USDT', 'VET/USDT', 'GALA/USDT']

# Using Public-Only Mode to bypass 451 errors
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'adjustForTimeDifference': True}
})

# Point to the Global GCP endpoint for public data
exchange.urls['api']['public'] = 'https://api-gcp.binance.com/api'

def send_mobile_alert(status_text, symbol, price, rsi, extra_info=""):
    try:
        title = f"{status_text}: {symbol}"
        message = f"Price: ${price}\nRSI: {rsi:.2f}\n{extra_info}"
        tag_list = "rocket" if "LONG" in status_text else "chart_with_downwards_trend"
        requests.post(f"https://ntfy.sh/{MY_TOPIC}", data=message.encode('utf-8'),
                     headers={"Title": title, "Priority": "5", "Tags": tag_list}, timeout=15)
    except: pass

def get_signals(symbol):
    try:
        # fetch_ohlcv is a PUBLIC call, which usually bypasses the 451 filter
        bars = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['rsi'] = 100 - (100 / (1 + (gain / loss)))
        
        last = df.iloc[-1]
        price, rsi, ema = last['close'], last['rsi'], last['ema20']

        if price > ema and 50 < rsi < 70: return "LONG", price, rsi, "Bullish"
        elif price < ema and 30 < rsi < 50: return "SHORT", price, rsi, "Bearish"
        return "NEUTRAL", price, rsi, ""
    except Exception as e:
        return f"Error: {str(e)[:50]}", 0, 0, ""

print("--- OneTrade007 EU-Bot (Public Mode) Starting ---")
sys.stdout.flush()

while True:
    print(f"\n--- Scan Started: {time.strftime('%H:%M:%S')} ---")
    for symbol in COINS:
        status, price, rsi, info = get_signals(symbol)
        print(f"{symbol}: {status} | Price: {price} | RSI: {rsi:.2f}")
        if status in ["LONG", "SHORT"]:
            send_mobile_alert(status, symbol, price, rsi, info)
        time.sleep(1)
    sys.stdout.flush()
    time.sleep(900)
