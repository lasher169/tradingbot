import concurrent.futures
import pandas_ta as ta
import yfinance as yf
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

tickers = []  # Add your list of tickers


# Function to detect EMA crossovers
def detect_crossovers(short_ema, long_ema):
    crossover_up = (short_ema > long_ema) & (short_ema.shift(1) <= long_ema.shift(1))
    crossover_down = (short_ema < long_ema) & (short_ema.shift(1) >= long_ema.shift(1))
    return crossover_up, crossover_down

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
    if df.size == 0:
        return None
    return df

# Function to check the latest crossover direction
def latest_crossover_direction(short_ema, long_ema, sustain_period=5):
    """
    Determine if the latest crossover is an upward trend (Golden Cross).

    Parameters:
        short_ema (pd.Series): Short-term Exponential Moving Average (EMA).
        long_ema (pd.Series): Long-term Exponential Moving Average (EMA).

    Returns:
        bool: True if the latest crossover is an upward trend, False otherwise.
    """
    # Identify crossover points

    try:
        golden_cross = (short_ema > long_ema) & (short_ema.shift(1) <= long_ema.shift(1))
        death_cross = (short_ema < long_ema) & (short_ema.shift(1) >= long_ema.shift(1))

        # Combine crossover points
        crossover_points = golden_cross | death_cross

        # Filter out rows where crossovers occur
        crossover_dates = crossover_points[crossover_points].index

        # If there are no crossovers, return False
        if len(crossover_dates) == 0:
            return False

        # Get the latest crossover date
        latest_crossover_date = crossover_dates[-1]

        # Check if the latest crossover is a Golden Cross
        if not golden_cross[latest_crossover_date]:
            return False

        # Ensure the short EMA has been above the long EMA for at least `sustain_period` days
        start_check_date = latest_crossover_date + pd.Timedelta(days=1)
        end_check_date = start_check_date + pd.Timedelta(days=sustain_period - 1)

        if end_check_date > short_ema.index[-1]:
            return False

        sustained = all(short_ema.loc[start_check_date:end_check_date] > long_ema.loc[start_check_date:end_check_date])

        return sustained
    except:
        return None

def golden_cross(short_ema, long_ema, period=5):
    """
    Determine if a Golden Cross (short EMA crosses above long EMA) occurs.

    Parameters:
        short_ema (pd.Series): Short-term Exponential Moving Average (EMA).
        long_ema (pd.Series): Long-term Exponential Moving Average (EMA).

    Returns:
        bool: True if a Golden Cross occurs, False otherwise.
    """
    try:
        crossover_condition = (short_ema > long_ema) & (short_ema.shift(1) <= long_ema.shift(1))
        return any(crossover_condition.rolling(window=period).sum() > 0)
    except:
        return None


upward_trending_stocks = []
downward_trending_stocks = []

def calc_ema(ticker):
    print("working on", ticker)
    df = get_stock_data(ticker)

    if df is not None:
        df['EMA_5'] = ta.ema(df["Close"], length=5)
        df['EMA_30'] = ta.ema(df["Close"], length=30)

        # Calculate On-Balance Volume (OBV)
        df['OBV'] = ta.obv(df['Close'], df['Volume'])

        # if is_upward_ema(df):
        #     print("adding ",ticker)
        #     upward_trending_stocks.append(ticker)

        trend_result = latest_crossover_direction(df['EMA_5'], df['EMA_30'], 10)
        if  trend_result is not None and trend_result:
            print("adding ",ticker)
            upward_trending_stocks.append(ticker)
            crossover_up, crossover_down = detect_crossovers(df['EMA_5'], df['EMA_30'])

            # Plotting the results (optional, requires matplotlib)
            import matplotlib.pyplot as plt


            plt.figure(figsize=(40, 7))
            plt.plot(df['Close'], label='Close Price', color='black')
            plt.plot(df['EMA_5'], label='5-day EMA', color='green')
            plt.plot(df['EMA_30'], label='30-day EMA', color='red')
            plt.xlabel('Date')
            plt.ylabel('Price')

            plt.twinx()
            plt.plot(df['OBV'], label='OBV', color='aqua', linestyle='--')

            plt.scatter(df.index[crossover_up], df['Close'][crossover_up], marker='^', color='green', label='Golden Cross',
                        s=100)
            plt.scatter(df.index[crossover_down], df['Close'][crossover_down], marker='v', color='red', label='Death Cross',
                        s=100)
            plt.legend()
            plt.title('EMA Crossover Strategy with OBV '+ticker)
            print("plotting ",ticker)
            plt.ion()
            plt.show()
            plt.pause(0.001)

        print("completed", ticker)
    else:
        print(ticker.upper(), "failed")

# Example usage

data = fetch_nasdaq_stocks()

tickers = process_tickers(data)

for ticker in tickers:
    # with concurrent.futures.ThreadPoolExecutor(max_workers=250) as executor:
    #     future = executor.submit(calc_ema(ticker))
    calc_ema("svco")



print("Upward trending stocks:", upward_trending_stocks)
