from sqlalchemy import Column, Integer, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class PriceHistory(Base):
  __tablename__ = "price_history"
  id = Column(Integer, primary_key=True)
  company_id = Column(Integer, ForeignKey("companies.id"))
  date = Column(Date, nullable=False, index=True)
  close = Column(Float, nullable=False)

  company = relationship("Company", back_populates="prices")
