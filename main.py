import ccxt
import pandas as pd
import time
import requests
import sys

# ==========================================
# FINAL CLOUD-SHELL CONFIG
# ==========================================
MY_TOPIC = "OneTrade007" 
COINS = ['DOGE/USDT', 'PIPPIN/USDT', 'POL/USDT', 'VET/USDT', 'GALA/USDT']

exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'adjustForTimeDifference': True}
})

# Use the "Data" subdomain - this is the 451-Bypass for Google Cloud
exchange.urls['api']['public'] = 'https://data.binance.com/api'

def send_mobile_alert(status_text, symbol, price, rsi, extra_info=""):
    try:
        title = f"{status_text}: {symbol}"
        message = f"Price: ${price}\nRSI: {rsi:.2f}\n{extra_info}"
        requests.post(f"https://ntfy.sh/{MY_TOPIC}", data=message.encode('utf-8'),
                     headers={"Title": title, "Priority": "5"}, timeout=15)
    except: pass

def get_signals(symbol):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['rsi'] = 100 - (100 / (1 + (gain / loss)))
        
        last = df.iloc[-1]
        return "NEUTRAL", last['close'], last['rsi'], ""
    except Exception as e:
        return f"Error: {str(e)[:30]}", 0, 0, ""

print("--- OneTrade007 Final Attempt (Data Mode) ---")
sys.stdout.flush()

while True:
    print(f"\n--- Scan Started: {time.strftime('%H:%M:%S')} ---")
    for symbol in COINS:
        status, price, rsi, info = get_signals(symbol)
        print(f"{symbol}: {status} | Price: {price} | RSI: {rsi:.2f}")
    sys.stdout.flush()
    time.sleep(900)
