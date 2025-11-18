import pmdarima as pm
from arch import arch_model
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings

FORECAST_DAYS = 10

MODEL_CONFIG = {
  "BOS.WA": {"order": (1, 1, 2), "seasonal_order": (1, 0, 1, 5)},
  "GTN.WA": {"order": (0, 1, 0), "seasonal_order": (0, 0, 0, 5)},
  "BHW.WA": {"order": (1, 1, 0), "seasonal_order": (0, 0, 0, 5)},
  "PKO.WA": {"order": (3, 1, 1), "seasonal_order": (0, 0, 0, 5)},
  "SPL.WA": {"order": (3, 1, 0), "seasonal_order": (0, 0, 1, 5)},
}

def train_and_predict(y: pd.Series, ticker: str) -> tuple[pd.Series | None, pd.Series | None]:
  if y.empty:
    return None, None

  print(f"Trenowanie modeli dla {ticker}...")
    
  arima_residuals = None
  arima_forecast = None

  try:
    if ticker in MODEL_CONFIG:
      params = MODEL_CONFIG[ticker]
      print(f"   -> Używanie zdefiniowanych parametrów: {params}")
                    
      model = SARIMAX(
        y,
        order=params["order"],
        seasonal_order=params["seasonal_order"],
        enforce_stationarity=False,
        enforce_invertibility=False
      )
      results = model.fit(disp=False)
                
      forecast_result = results.get_forecast(steps=FORECAST_DAYS)
      arima_forecast = forecast_result.predicted_mean
      arima_residuals = results.resid
          
    else:
      print("   -> Parametry nieznane, uruchamianie auto_arima...")
      auto_model = pm.auto_arima(
        y,
        start_p=1, start_q=1,
        max_p=3, max_q=3,
        m=5, d=1,             
        trace=False,
        error_action='ignore',  
        suppress_warnings=True, 
        stepwise=True
      )
      arima_forecast = auto_model.predict(n_periods=FORECAST_DAYS)
      arima_residuals = auto_model.resid()

  except Exception as e:
    print(f"Błąd ARIMA dla {ticker}: {e}")
    return None, None

  garch_vol = None
  try:
    residuals_scaled = arima_residuals.dropna() * 100
            
    if residuals_scaled.std() == 0:
      print(f"   -> Ostrzeżenie: Reszty są stałe, pomijanie GARCH.")        
      garch_vol = pd.Series([0]*FORECAST_DAYS, index=arima_forecast.index)
    else:
      garch_model = arch_model(residuals_scaled, mean='Zero', vol='Garch', p=1, q=1)
      garch_results = garch_model.fit(disp='off')
          
      garch_forecast_res = garch_results.forecast(horizon=FORECAST_DAYS)
          
      garch_vol = (garch_forecast_res.variance.iloc[-1]**0.5) / 100
          
      garch_vol.index = arima_forecast.index

  except Exception as e:
    print(f"Błąd GARCH dla {ticker}: {e}")
    return arima_forecast, None

  return arima_forecast, garch_vol
