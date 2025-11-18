import yfinance as yf
import pandas as pd
from datetime import date, datetime

def download_stock_data(ticker: str, start_date: date) -> pd.DataFrame:
  print(f"Pobieranie danych dla: {ticker} od {start_date}")
  try:
    start_str = start_date.strftime('%Y-%m-%d')
    
    df = yf.download(
      ticker, 
      start=start_str, 
      end=datetime.now(), 
      progress=False,
      auto_adjust=True
    )

    if df.empty:
      return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    if 'Close' not in df.columns:
      return pd.DataFrame()
      
    df = df.reset_index()
        
    if 'Date' not in df.columns:    
      for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
          df.rename(columns={col: 'Date'}, inplace=True)
          break

    return df[['Date', 'Close']]
    
  except Exception as e:
    print(f"Błąd yfinance dla {ticker}: {e}")
    return pd.DataFrame()
