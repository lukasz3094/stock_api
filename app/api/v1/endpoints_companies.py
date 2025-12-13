from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.price_history import PriceHistory
from app.schemas.company import CompanyWithPrice
from app.schemas.price_history import PriceHistoryPublic
from typing import List
import io
import pandas as pd
from fastapi.responses import StreamingResponse


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
  # Check if company exists first
  company_result = await db.execute(select(Company).where(Company.ticker == ticker.upper()))
  company = company_result.scalar_one_or_none()

  if not company:
    raise HTTPException(status_code=404, detail="Company not found")

  # Original logic for fetching history
  result = await db.execute(
      select(PriceHistory)
      .where(PriceHistory.company_id == company.id)
      .order_by(PriceHistory.date)
  )
  return result.scalars().all()


@router.get("/companies/{ticker}/history/download")
async def download_company_history(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if company exists first
    company_result = await db.execute(select(Company).where(Company.ticker == ticker.upper()))
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Original logic for fetching history
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.company_id == company.id)
        .order_by(PriceHistory.date)
    )
    history = result.scalars().all()

    if not history:
        raise HTTPException(status_code=404, detail="No history found for this company")

    df = pd.DataFrame([
        {'date': h.date, 'close': h.close} for h in history
    ])

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={ticker}_history.csv"
    return response
