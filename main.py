import os
import time
import requests
import pandas as pd
import pandas_ta as ta
import yfinance as yf

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", "GBPJPY=X"]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

def analyze_market(pair_symbol):
    try:
        df_h1 = yf.download(pair_symbol, period="7d", interval="1h", progress=False)
        df_m5 = yf.download(pair_symbol, period="2d", interval="5m", progress=False)

        if df_h1.empty or df_m5.empty:
            return

        if isinstance(df_h1.columns, pd.MultiIndex):
            df_h1.columns = df_h1.columns.get_level_values(0)
        if isinstance(df_m5.columns, pd.MultiIndex):
            df_m5.columns = df_m5.columns.get_level_values(0)

        # Indicators
        df_h1['EMA_50'] = ta.ema(df_h1['Close'], length=50)
        df_m5['EMA_20'] = ta.ema(df_m5['Close'], length=20)
        df_m5['RSI'] = ta.rsi(df_m5['Close'], length=14)

        current_price = float(df_m5['Close'].iloc[-1])
        rsi = float(df_m5['RSI'].iloc[-1])
        h1_ema = float(df_h1['EMA_50'].iloc[-1])

        # Breakout Levels
        recent_high = float(df_m5['High'].tail(15).max())
        recent_low = float(df_m5['Low'].tail(15).min())

        # SMC Liquidity Levels
        bsl = float(df_h1['High'].tail(30).max())
        ssl = float(df_h1['Low'].tail(30).min())

        m5_prev_low = float(df_m5['Low'].iloc[-2])
        m5_prev_high = float(df_m5['High'].iloc[-2])

        ssl_swept = m5_prev_low <= ssl and current_price > ssl
        bsl_swept = m5_prev_high >= bsl and current_price < bsl

        pair_clean = pair_symbol.replace("=X", "")

        # BUY SIGNAL LOGIC
        if (current_price > h1_ema and rsi > 45) and (ssl_swept or current_price > recent_high):
            sl = current_price - (current_price * 0.0015)
            tp = current_price + (current_price * 0.0030)
            reason = "SSL Liquidity Sweep + RSI/EMA Confirmation" if ssl_swept else "M5 Resistance Breakout + H1 Trend"

            msg = (
                f"🟢 **FOREX BUY SIGNAL** 🟢\n\n"
                f"💱 **Pair:** {pair_clean}\n"
                f"📊 **Strategy:** SMC (Liquidity) + Breakout + RSI/EMA\n"
                f"🎯 **Setup:** {reason}\n"
                f"📍 **Entry:** {current_price:.5f}\n"
                f"🔴 **Stop Loss (SL):** {sl:.5f}\n"
                f"🟢 **Take Profit (TP):** {tp:.5f}\n\n"
                f"⏰ **Timeframe:** H1 Trend ➔ M5 Entry"
            )
            send_telegram_message(msg)

        # SELL SIGNAL LOGIC
        elif (current_price < h1_ema and rsi < 55) and (bsl_swept or current_price < recent_low):
            sl = current_price + (current_price * 0.0015)
            tp = current_price - (current_price * 0.0030)
            reason = "BSL Liquidity Sweep + RSI/EMA Confirmation" if bsl_swept else "M5 Support Breakout + H1 Trend"

            msg = (
                f"🔴 **FOREX SELL SIGNAL** 🔴\n\n"
                f"💱 **Pair:** {pair_clean}\n"
                f"📊 **Strategy:** SMC (Liquidity) + Breakout + RSI/EMA\n"
                f"🎯 **Setup:** {reason}\n"
                f"📍 **Entry:** {current_price:.5f}\n"
                f"🔴 **Stop Loss (SL):** {sl:.5f}\n"
                f"🟢 **Take Profit (TP):** {tp:.5f}\n\n"
                f"⏰ **Timeframe:** H1 Trend ➔ M5 Entry"
            )
            send_telegram_message(msg)

    except Exception as e:
        print(f"Error checking {pair_symbol}: {e}")

if __name__ == "__main__":
    send_telegram_message("🚀 **Forex Multi-Strategy Bot (BUY/SELL) ya tashi 24/7!**")
    while True:
        for pair in PAIRS:
            analyze_market(pair)
            time.sleep(2)
        time.sleep(300)
