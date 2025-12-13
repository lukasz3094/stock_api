import pmdarima as pm
from arch import arch_model
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

FORECAST_DAYS = 10

MODEL_CONFIG = {}


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
          max_p=5, max_q=5,
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
      garch_model = arch_model(
          residuals_scaled, mean='Zero', vol='Garch', p=1, q=1)
      garch_results = garch_model.fit(disp='off')

      garch_forecast_res = garch_results.forecast(horizon=FORECAST_DAYS)

      garch_vol = (garch_forecast_res.variance.iloc[-1]**0.5) / 100

      garch_vol.index = arima_forecast.index

  except Exception as e:
    print(f"Błąd GARCH dla {ticker}: {e}")
    return arima_forecast, None

  return arima_forecast, garch_vol


def train_and_predict_lstm(y: pd.Series, ticker: str) -> pd.Series | None:
    if y.empty:
        return None

    print(f"Trenowanie modelu LSTM dla {ticker}...")

    try:
        # Preprocessing
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(y.values.reshape(-1, 1))

        # Create dataset
        def create_dataset(dataset, time_step=1):
            dataX, dataY = [], []
            for i in range(len(dataset) - time_step - 1):
                a = dataset[i:(i + time_step), 0]
                dataX.append(a)
                dataY.append(dataset[i + time_step, 0])
            return np.array(dataX), np.array(dataY)

        time_step = 60
        X_train, y_train = create_dataset(scaled_data, time_step)

        # Reshape input to be [samples, time steps, features]
        X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)

        # Build LSTM model
        model = Sequential()
        model.add(LSTM(50, return_sequences=True, input_shape=(time_step, 1)))
        model.add(LSTM(50, return_sequences=False))
        model.add(Dense(25))
        model.add(Dense(1))

        model.compile(optimizer='adam', loss='mean_squared_error')

        # Train the model
        model.fit(X_train, y_train, batch_size=1, epochs=1)

        # Prediction
        temp_input = list(scaled_data[-time_step:].flatten())
        lst_output = []
        n_steps = time_step
        i = 0
        while i < FORECAST_DAYS:
            if len(temp_input) > n_steps:
                x_input = np.array(temp_input[1:])
                x_input = x_input.reshape((1, n_steps, 1))
                yhat = model.predict(x_input, verbose=0)
                temp_input.append(yhat[0][0])
                temp_input = temp_input[1:]
                lst_output.append(yhat[0][0])
                i = i + 1
            else:
                x_input = np.array(temp_input)
                x_input = x_input.reshape((1, n_steps, 1))
                yhat = model.predict(x_input, verbose=0)
                temp_input.append(yhat[0][0])
                lst_output.append(yhat[0][0])
                i = i + 1
        
        # Inverse transform to get actual prices
        predictions = scaler.inverse_transform(np.array(lst_output).reshape(-1, 1)).flatten()

        # Create a pandas Series with a DatetimeIndex
        last_date = y.index[-1]
        future_dates = pd.to_datetime(pd.date_range(start=last_date + pd.Timedelta(days=1), periods=FORECAST_DAYS, freq='D'))
        lstm_forecast = pd.Series(predictions, index=future_dates)

        return lstm_forecast

    except Exception as e:
        print(f"Błąd LSTM dla {ticker}: {e}")
        return None