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

# Clean setup for Europe/Asia servers
exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True
})

def send_mobile_alert(status_text, symbol, price, rsi, extra_info=""):
    try:
        title = f"{status_text}: {symbol}"
        message = f"Price: ${price}\nRSI: {rsi:.2f}\n{extra_info}"
        tag_list = "rocket" if "LONG" in status_text else "chart_with_downwards_trend"
        if "ONLINE" in status_text: tag_list = "white_check_mark"

        requests.post(
            f"https://ntfy.sh/{MY_TOPIC}",
            data=message.encode('utf-8'),
            headers={"Title": title, "Priority": "5", "Tags": tag_list},
            timeout=15 
        )
    except Exception as e:
        print(f"Notification Error: {e}")

def get_signals(symbol):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['rsi'] = 100 - (100 / (1 + (gain / loss)))
        
        df['tr'] = df[['high', 'low', 'close']].max(axis=1) - df[['high', 'low', 'close']].min(axis=1)
        df['atr'] = df['tr'].rolling(14).mean()

        last = df.iloc[-1]
        price, rsi, ema, atr = last['close'], last['rsi'], last['ema20'], last['atr']

        if price > ema and 50 < rsi < 70:
            return "LONG", price, rsi, f"🎯 SL: ${price - (atr * 1.5):.4f}"
        elif price < ema and 30 < rsi < 50:
            return "SHORT", price, rsi, f"🎯 SL: ${price + (atr * 1.5):.4f}"
        
        return "NEUTRAL", price, rsi, ""
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return "Error", 0, 0, ""

print("--- OneTrade007 EU-Bot is starting ---")
sys.stdout.flush()
send_mobile_alert("EU-CLOUD ONLINE", "All Systems", "Bot is live from Europe/Asia!", 0.0)

while True:
    print(f"\n--- Scan Started: {time.strftime('%H:%M:%S')} ---")
    for symbol in COINS:
        status, price, rsi, extra = get_signals(symbol)
        print(f"{symbol}: {status} (Price: {price}, RSI: {rsi:.2f})")
        if status in ["LONG", "SHORT"]:
            send_mobile_alert(status, symbol, price, rsi, extra)
        time.sleep(2) 
    
    sys.stdout.flush()
    time.sleep(900)