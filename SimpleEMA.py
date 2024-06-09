import concurrent.futures
import pandas_ta as ta
import yfinance as yf
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
from contextlib import redirect_stdout

tickers = []  # Add your list of tickers


def process_tickers(data):
    tickers = []
    rows =  data.get('data').get('table').get('rows', {})
    print()
    for row in rows:
        tickers.append(row.get('symbol'))
    return tickers

def fetch_nasdaq_stocks():
    url = "https://api.nasdaq.com/api/screener/stocks"
    params = {
        "limit": 4050,
        "exchange": "nasdaq"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()
        return data
    except requests.exceptions.Timeout:
        print("The request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


# Fetch and print the NASDAQ stock data
nasdaq_data = fetch_nasdaq_stocks()

if nasdaq_data:
    print(nasdaq_data)

def get_stock_data(ticker):
    current_date = datetime.today()
    df = yf.download(ticker, period="3mo", interval="1d", start = current_date - relativedelta(months=4), end=current_date)

    return df

def calculate_ema(df, length=30):
    df["EMA"] = ta.ema(df["Close"], length=length)
    return df

def is_upward_ema(df, length=30):
    ema = df["EMA"].tail(length)
    return all(ema.iloc[i] < ema.iloc[i + 1] for i in range(len(ema) - 1))

upward_trending_stocks = []
def calc_ema(ticker):
    print("working on", ticker)
    df = get_stock_data(ticker)
    df = calculate_ema(df)
    if is_upward_ema(df):
        print("adding ",ticker)
        upward_trending_stocks.append(ticker)
    print("completed", ticker)

# Example usage

data = fetch_nasdaq_stocks()

tickers = process_tickers(data)

for ticker in tickers:
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        future = executor.submit(calc_ema(ticker))



print("Upward trending stocks:", upward_trending_stocks)
