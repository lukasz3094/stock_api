from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import List, Union


class ArimaPredictionOut(BaseModel):
  target_date: date
  predicted_value: float
  model_config = ConfigDict(from_attributes=True)


class GarchPredictionOut(BaseModel):
  target_date: date
  predicted_volatility: float
  model_config = ConfigDict(from_attributes=True)


class LstmPredictionOut(BaseModel):
  target_date: date
  predicted_value: float
  model_config = ConfigDict(from_attributes=True)


class DashboardData(BaseModel):
  ticker: str
  last_update: date
  arima_forecast: List[ArimaPredictionOut]
  garch_forecast: List[GarchPredictionOut]
  lstm_forecast: List[LstmPredictionOut]


class ModelPredictions(BaseModel):
  ticker: str
  model_name: str
  last_update: date
  forecast: Union[List[ArimaPredictionOut], List[LstmPredictionOut]]


class ArimaPredictionCreate(BaseModel):
  company_id: int
  forecast_date: date
  target_date: date
  predicted_value: float


class GarchPredictionCreate(BaseModel):
  company_id: int
  forecast_date: date
  target_date: date
  predicted_volatility: float


class LstmPredictionCreate(BaseModel):
  company_id: int
  forecast_date: date
  target_date: date
  predicted_value: float
