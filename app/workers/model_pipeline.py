import pmdarima as pm
from arch import arch_model
import pandas as pd
from .data_loader import get_stock_data
from datetime import date, timedelta

FORECAST_DAYS = 10

def run_prediction_pipeline(ticker: str) -> tuple[pd.Series | None, pd.Series | None]:
  y = get_stock_data(ticker)
  if y.empty:
    print(f"Brak danych dla {ticker}, pomijanie.")
    return None, None

  print(f"Uruchamianie auto_arima dla {ticker} (m=5)...")
    
  try:
    auto_model = pm.auto_arima(
      y,
      start_p=1, start_q=1,
      test='adf',
      max_p=3, max_q=3,
      m=5,
      start_P=0, 
      D=0,
      trace=False,
      error_action='ignore',  
      suppress_warnings=True, 
      stepwise=True
    )
  except Exception as e:
    print(f"Błąd auto_arima dla {ticker}: {e}")
    return None, None

  print(f"Znaleziony model ARIMA: {auto_model.order}x{auto_model.seasonal_order}")

  residuals = auto_model.resid().dropna()
  residuals = residuals * 100

  try:
    garch_model = arch_model(residuals, mean='Zero', vol='Garch', p=1, q=1)
    garch_results = garch_model.fit(disp='off')
        
    if garch_results.pvalues['alpha[1]'] > 0.1 and garch_results.pvalues['beta[1]'] > 0.1:
      print(f"Model GARCH nieistotny dla {ticker}, zmienność może być stała.")        
            
  except Exception as e:
    print(f"Błąd GARCH dla {ticker}: {e}")
    return None, None

  print(f"Model GARCH wytrenowany dla {ticker}.")

  arima_forecast_series = auto_model.predict(n_periods=FORECAST_DAYS)
  garch_forecast = garch_results.forecast(horizon=FORECAST_DAYS)
  
  garch_vol_series = (garch_forecast.variance.iloc[-1]**0.5) / 100
  
  garch_vol_series.index = arima_forecast_series.index

  return arima_forecast_series, garch_vol_series
