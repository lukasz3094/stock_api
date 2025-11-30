from pydantic import BaseModel, ConfigDict
from datetime import date


class PriceHistoryBase(BaseModel):
  date: date
  close: float


class PriceHistoryPublic(PriceHistoryBase):
  id: int
  model_config = ConfigDict(from_attributes=True)
