import asyncio
import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from sqlalchemy import delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta, datetime

from app.db.session import AsyncSessionLocal
from app.models.company import Company
from app.models.predictions import PredictionArima, PredictionGarch, PriceHistory
from .data_loader import download_stock_data
from .model_pipeline import train_and_predict

scheduler = AsyncIOScheduler()

async def run_nightly_prediction_job(db: AsyncSession | None = None, tickers=None):
  print(f"[{datetime.now()}] Uruchamianie Nocnego Joba...")

  if db is None:
    async with AsyncSessionLocal() as session:
      return await run_nightly_prediction_job(db=session, tickers=tickers)

  print("JOB SESSION:", id(db))

  query = select(Company.id, Company.ticker)
  if tickers:
    query = query.where(Company.ticker.in_(tickers))

  result = await db.execute(query)
  companies_data = result.all()

  today = date.today()
  DEFAULT_START = date(2020, 1, 1)

  for company_id, company_ticker in companies_data:
    print(f"--- Przetwarzanie: {company_ticker} ---")

    last_entry_q = await db.execute(
      select(PriceHistory.date)
      .where(PriceHistory.company_id == company_id)
      .order_by(desc(PriceHistory.date))
      .limit(1)
    )
    last_date = last_entry_q.scalar_one_or_none()

    start_download_date = DEFAULT_START
    if last_date:
      start_download_date = last_date + timedelta(days=1)

    if start_download_date < today:
      try:
        new_data_df = await asyncio.to_thread(
          download_stock_data, company_ticker, start_download_date
        )
        if not new_data_df.empty:
          for _, row in new_data_df.iterrows():
            current_date = pd.to_datetime(row['Date']).date()
            if last_date and current_date <= last_date:
              continue
            ph = PriceHistory(
              company_id=company_id,
              date=current_date,
              close=row['Close']
            )
            db.add(ph)
          await db.commit()
      except Exception:
        pass

    history_q = await db.execute(
      select(PriceHistory)
      .where(PriceHistory.company_id == company_id)
      .order_by(PriceHistory.date)
    )
    history_rows = history_q.scalars().all()

    if not history_rows:
      continue

    df_full = pd.DataFrame([
      {'Date': h.date, 'y': h.close} for h in history_rows
    ])
    df_full['Date'] = pd.to_datetime(df_full['Date'])
    df_full.set_index('Date', inplace=True)
    series_clean = df_full['y'].asfreq('B').ffill()

    try:
      arima_forecast, garch_forecast = await asyncio.to_thread(
        train_and_predict, series_clean, company_ticker
      )
    except Exception:
      continue

    if arima_forecast is None:
      continue

    await db.execute(delete(PredictionArima).where(PredictionArima.company_id == company_id))
    await db.execute(delete(PredictionGarch).where(PredictionGarch.company_id == company_id))

    for i in range(len(arima_forecast)):
      target_dt = today + timedelta(days=i+1)
      db.add(PredictionArima(
        company_id=company_id,
        forecast_date=today,
        target_date=target_dt,
        predicted_value=arima_forecast.iloc[i]
      ))
      if garch_forecast is not None:
        db.add(PredictionGarch(
          company_id=company_id,
          forecast_date=today,
          target_date=target_dt,
          predicted_volatility=garch_forecast.iloc[i]
        ))

    await db.commit()
    print(f"Zapisano prognozy dla {company_ticker}")

  print(f"[{datetime.now()}] Nocny Job zakończony.")

def setup_scheduler():
  scheduler.add_job(run_nightly_prediction_job, 'cron', hour=1, minute=0)
  scheduler.start()
