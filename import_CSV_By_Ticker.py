import yfinance as yf
from datetime import datetime

symbol = "GOOG"
start_date = "2023-01-01"
end_date = datetime.now().strftime('%Y-%m-%d')  # Today's date in 'YYYY-MM-DD' format
interval = "1h"
data = yf.download(symbol, start=start_date, end=end_date, interval=interval)
data.to_csv('GOOGLE_1H_01.01.2023-Today.csv')