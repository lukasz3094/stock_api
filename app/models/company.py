from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class Company(Base):
  __tablename__ = "companies"
  id = Column(Integer, primary_key=True, index=True)
  name = Column(String, unique=True, nullable=False)
  ticker = Column(String, unique=True, index=True, nullable=False)
  
  # prices = relationship("PriceHistory", back_populates="company")
  arima_predictions = relationship("PredictionArima", back_populates="company")
  garch_predictions = relationship("PredictionGarch", back_populates="company")