# --- fetch_data.py ---
import yfinance as yf
import pandas as pd
from datetime import datetime
import os

# נתיב חדש לשמירת הקבצים
SAVE_DIRECTORY = r"D:\\PROJECTS\\TRADES"

def calculate_rsi_wilder(data, period=14):
    delta = data['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_cci(data, period=5):
    tp = (data['High'] + data['Low'] + data['Close']) / 3
    sma = tp.rolling(window=period).mean()
    mad = tp.rolling(window=period).apply(lambda x: abs(x - x.mean()).mean(), raw=False)
    cci = (tp - sma) / (0.015 * mad)
    return cci

def calculate_bollinger_bands(data, period=20, std_multiplier=2):
    ma = data['Close'].rolling(window=period).mean()
    std = data['Close'].rolling(window=period).std()
    upper = ma + (std_multiplier * std)
    lower = ma - (std_multiplier * std)
    return upper, ma, lower

def fetch_stock_data(ticker, start, end, interval="1d"):
    try:
        data = yf.download(ticker, start=start, end=end, interval=interval)
        if data.empty:
            return None

        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in data.columns for col in required_columns):
            return None

        data = data[required_columns]

        if len(data) >= 20:
            data["RSI"] = calculate_rsi_wilder(data)
            data["CCI"] = calculate_cci(data)
            bb_top, bb_mid, bb_bot = calculate_bollinger_bands(data)
            data["Bollinger Top"] = bb_top
            data["Bollinger Mid"] = bb_mid
            data["Bollinger Bottom"] = bb_bot

        data.reset_index(inplace=True)

        os.makedirs(SAVE_DIRECTORY, exist_ok=True)
        filename = os.path.join(SAVE_DIRECTORY, f"{ticker}_{start}_{end}.csv")
        data.to_csv(filename, index=False)
        return filename

    except Exception as e:
        print(f"Error fetching data: {e}")
        return None
