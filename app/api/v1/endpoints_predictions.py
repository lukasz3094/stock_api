from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.prediction_arima import PredictionArima
from app.models.prediction_garch import PredictionGarch
from app.models.prediction_lstm import PredictionLstm
from app.schemas.predictions import DashboardData, ModelPredictions
from datetime import date
from sqlalchemy import desc, func
from typing import List

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
          selectinload(Company.garch_predictions),
          selectinload(Company.lstm_predictions)
      )
  )
  company = result.scalar_one_or_none()

  if not company:
    raise HTTPException(status_code=404, detail="Company not found")

  latest_arima_date_q = await db.execute(
      select(func.max(PredictionArima.forecast_date))
      .where(PredictionArima.company_id == company.id)
  )
  latest_garch_date_q = await db.execute(
      select(func.max(PredictionGarch.forecast_date))
      .where(PredictionGarch.company_id == company.id)
  )
  latest_lstm_date_q = await db.execute(
      select(func.max(PredictionLstm.forecast_date))
      .where(PredictionLstm.company_id == company.id)
  )
  
  dates = [
      latest_arima_date_q.scalar_one_or_none(),
      latest_garch_date_q.scalar_one_or_none(),
      latest_lstm_date_q.scalar_one_or_none()
  ]
  
  latest_forecast_date = max(d for d in dates if d is not None)

  if latest_forecast_date is None:
    raise HTTPException(
        status_code=404, detail="No predictions found for this company yet.")

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

  lstm_results = await db.execute(
      select(PredictionLstm)
      .where(PredictionLstm.company_id == company.id)
      .where(PredictionLstm.forecast_date == latest_forecast_date)
      .order_by(PredictionLstm.target_date)
      .limit(FORECAST_DAYS)
  )

  arima_forecasts = arima_results.scalars().all()
  garch_forecasts = garch_results.scalars().all()
  lstm_forecasts = lstm_results.scalars().all()

  if not arima_forecasts and not garch_forecasts and not lstm_forecasts:
    raise HTTPException(
        status_code=404, detail="No predictions found for this company yet.")

  last_update_date = latest_forecast_date

  return {
      "ticker": company.ticker,
      "last_update": last_update_date,
      "arima_forecast": arima_forecasts,
      "garch_forecast": garch_forecasts,
      "lstm_forecast": lstm_forecasts
  }


@router.get("/predictions/{ticker}/{model_name}", response_model=ModelPredictions)
async def get_model_predictions(
    ticker: str,
    model_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if model_name.lower() not in ["arima", "lstm"]:
        raise HTTPException(status_code=400, detail="Invalid model name. Choose 'arima' or 'lstm'.")

    company_result = await db.execute(select(Company).where(Company.ticker == ticker.upper()))
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    model_map = {
        "arima": PredictionArima,
        "lstm": PredictionLstm,
    }

    prediction_model = model_map.get(model_name.lower())
    
    latest_forecast_date_q = await db.execute(
        select(func.max(prediction_model.forecast_date))
        .where(prediction_model.company_id == company.id)
    )
    latest_forecast_date = latest_forecast_date_q.scalar_one_or_none()

    if not latest_forecast_date:
        raise HTTPException(status_code=404, detail=f"No {model_name} predictions found for this company")

    results = await db.execute(
        select(prediction_model)
        .where(prediction_model.company_id == company.id)
        .where(prediction_model.forecast_date == latest_forecast_date)
        .order_by(prediction_model.target_date)
    )

    predictions = results.scalars().all()

    if not predictions:
        raise HTTPException(status_code=404, detail=f"No {model_name} predictions found for this company")

    return ModelPredictions(
        ticker=company.ticker,
        model_name=model_name,
        last_update=latest_forecast_date,
        forecast=predictions
    )
