from pydantic import BaseModel, ConfigDict

class CompanyBase(BaseModel):
  name: str
  ticker: str

class CompanyPublic(CompanyBase):
  id: int
  model_config = ConfigDict(from_attributes=True)