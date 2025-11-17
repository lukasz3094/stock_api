from pydantic import BaseModel, ConfigDict
from datetime import date

class ArimaPredictionOut(BaseModel):
  target_date: date
  predicted_value: float
  model_config = ConfigDict(from_attributes=True)

class GarchPredictionOut(BaseModel):
  target_date: date
  predicted_volatility: float
  model_config = ConfigDict(from_attributes=True)

class DashboardData(BaseModel):
  ticker: str
  last_update: date
  arima_forecast: list[ArimaPredictionOut]
  garch_forecast: list[GarchPredictionOut]