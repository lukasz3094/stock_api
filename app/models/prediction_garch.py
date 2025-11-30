from sqlalchemy import Column, Integer, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class PredictionGarch(Base):
  __tablename__ = "predictions_garch"
  id = Column(Integer, primary_key=True)
  company_id = Column(Integer, ForeignKey("companies.id"))
  forecast_date = Column(Date, index=True)
  target_date = Column(Date)
  predicted_volatility = Column(Float)

  company = relationship("Company", back_populates="garch_predictions")
