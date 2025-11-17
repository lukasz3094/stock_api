import yfinance as yf
import pandas as pd
from datetime import datetime

def get_stock_data(ticker: str, start_date: str = "2020-01-01") -> pd.Series:
  print(f"Pobieranie danych dla: {ticker} (using yfinance)")
  try:
    df = yf.download(ticker, start=start_date, end=datetime.now())
      
    if df.empty:
      raise Exception("Nie zwrócono danych z yfinance (sprawdź ticker?)")

    if 'Close' not in df.columns:
      raise Exception("Brak kolumny 'Close' w danych z yfinance.")
    
    series = df[['Close']]
    series.name = "y"
   
    series.index = pd.to_datetime(series.index)
    series_resampled = series.resample('B').ffill().bfill()
    
    if series_resampled.isnull().all().item():
      raise Exception("Wszystkie wartości są NaN po resamplingu.")
    
    return series_resampled
      
  except Exception as e:
    print(f"Błąd podczas pobierania danych (yfinance) dla {ticker}: {e}")
    return pd.Series(dtype='float64')
