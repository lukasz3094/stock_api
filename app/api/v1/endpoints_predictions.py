from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.predictions import PredictionArima, PredictionGarch
from app.schemas.predictions import DashboardData
from datetime import date
from sqlalchemy import desc, func

router = APIRouter()

FORECAST_DAYS = 10

@router.get("/predictions/{ticker}", response_model=DashboardData)
async def get_predictions_for_ticker(
  ticker: str,
  db: AsyncSession = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  result = await db.execute(
    select(Company)
    .where(Company.ticker == ticker.upper())
    .options(
      selectinload(Company.arima_predictions),
      selectinload(Company.garch_predictions)
    )
  )
  company = result.scalar_one_or_none()
    
  if not company:
    raise HTTPException(status_code=404, detail="Company not found")
  
  latest_forecast_date_q = await db.execute(
    select(func.max(PredictionArima.forecast_date))
    .where(PredictionArima.company_id == company.id)
  )
  latest_forecast_date = latest_forecast_date_q.scalar_one_or_none()
  
  if latest_forecast_date is None:
    raise HTTPException(status_code=404, detail="No predictions found for this company yet.")
  
  arima_results = await db.execute(
    select(PredictionArima)
    .where(PredictionArima.company_id == company.id)
    .where(PredictionArima.forecast_date == latest_forecast_date)
    .order_by(PredictionArima.target_date)
    .limit(FORECAST_DAYS)
  )
  
  garch_results = await db.execute(
    select(PredictionGarch)
    .where(PredictionGarch.company_id == company.id)
    .where(PredictionGarch.forecast_date == latest_forecast_date)
    .order_by(PredictionGarch.target_date)
    .limit(FORECAST_DAYS)
  )
  
  arima_forecasts = arima_results.scalars().all()
  garch_forecasts = garch_results.scalars().all()

  if not arima_forecasts:
    raise HTTPException(status_code=404, detail="No predictions found for this company yet.")

  last_update_date = arima_forecasts[0].forecast_date
  
  return {
    "ticker": company.ticker,
    "last_update": last_update_date,
    "arima_forecast": arima_forecasts,
    "garch_forecast": garch_forecasts
  }
