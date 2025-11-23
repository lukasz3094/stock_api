from pydantic import BaseModel, ConfigDict
from typing import Optional

class CompanyBase(BaseModel):
  name: str
  ticker: str

class CompanyPublic(CompanyBase):
  id: int
  model_config = ConfigDict(from_attributes=True)
  
class CompanyWithPrice(CompanyPublic):
  current_price: Optional[float] = None
  price_change: Optional[float] = None