from pydantic import BaseModel
from typing import List

class PredictionInput(BaseModel):
    target_date: str
    predicted_value: float

class GarchInput(BaseModel):
    target_date: str
    predicted_volatility: float

class InterpretInput(BaseModel):
    arima_forecast: List[PredictionInput]
    garch_forecast: List[GarchInput]
