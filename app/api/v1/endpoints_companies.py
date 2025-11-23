from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.predictions import PriceHistory
from app.schemas.company import CompanyWithPrice
from app.schemas.price_history import PriceHistoryPublic
from typing import List

router = APIRouter()

@router.get("/companies", response_model=List[CompanyWithPrice])
async def get_all_companies(
  db: AsyncSession = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  result = await db.execute(select(Company))
  companies = result.scalars().all()
  
  companies_with_prices = []
  for company in companies:
    price_result = await db.execute(
      select(PriceHistory)
      .where(PriceHistory.company_id == company.id)
      .order_by(desc(PriceHistory.date))
      .limit(2)
    )
    prices = price_result.scalars().all()
    
    current_price = None
    price_change = None
    if prices and len(prices) > 0:
      current_price = prices[0].close
      if len(prices) > 1:
        price_change = prices[0].close - prices[1].close
        
    companies_with_prices.append(
      CompanyWithPrice(
        id=company.id,
        name=company.name,
        ticker=company.ticker,
        current_price=current_price,
        price_change=price_change,
      )
    )
    
  return companies_with_prices

@router.get("/companies/{ticker}/history", response_model=List[PriceHistoryPublic])
async def get_company_history(
  ticker: str,
  db: AsyncSession = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  result = await db.execute(
    select(PriceHistory)
    .join(Company)
    .where(Company.ticker == ticker.upper())
    .order_by(PriceHistory.date)
  )
  return result.scalars().all()
