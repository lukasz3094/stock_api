from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class PredictionArima(Base):
  __tablename__ = "predictions_arima"
  id = Column(Integer, primary_key=True)
  company_id = Column(Integer, ForeignKey("companies.id"))
  forecast_date = Column(Date, index=True)
  target_date = Column(Date)
  predicted_value = Column(Float)
  
  company = relationship("Company", back_populates="arima_predictions")

class PredictionGarch(Base):
  __tablename__ = "predictions_garch"
  id = Column(Integer, primary_key=True)
  company_id = Column(Integer, ForeignKey("companies.id"))
  forecast_date = Column(Date, index=True)
  target_date = Column(Date)
  predicted_volatility = Column(Float)
  
  company = relationship("Company", back_populates="garch_predictions")
  
class PriceHistory(Base):
  __tablename__ = "price_history"
  id = Column(Integer, primary_key=True)
  company_id = Column(Integer, ForeignKey("companies.id"))
  date = Column(Date, nullable=False, index=True)
  close = Column(Float, nullable=False)
  
  company = relationship("Company", back_populates="prices")
