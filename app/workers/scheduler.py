import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.models.company import Company
from app.models.predictions import PredictionArima, PredictionGarch
from .model_pipeline import run_prediction_pipeline
from datetime import date, timedelta, datetime
from sqlalchemy import delete

scheduler = AsyncIOScheduler()

async def run_nightly_prediction_job():
  print(f"[{datetime.now()}] Uruchamianie Nocnego Joba: Trenowanie modeli...")
    
  async with AsyncSessionLocal() as db:
    result = await db.execute(select(Company))
    companies = result.scalars().all()
      
    today = date.today()

    for company in companies:
      print(f"Przetwarzanie: {company.ticker}")
                  
      try:
        arima_forecast, garch_forecast = await asyncio.to_thread(
          run_prediction_pipeline, company.ticker
        )
      except Exception as e:
        print(f"KRYTYCZNY BŁĄD PIPELINE dla {company.ticker}: {e}")
        continue

      if arima_forecast is None or garch_forecast is None:
        continue
        
      await db.execute(delete(PredictionArima).where(PredictionArima.company_id == company.id))
      await db.execute(delete(PredictionGarch).where(PredictionGarch.company_id == company.id))

      for i in range(len(arima_forecast)):
        print(f"Dodawanie prognozy na dzień: {today + timedelta(days=i+1)}")
        target_dt = today + timedelta(days=i+1)

        db_arima = PredictionArima(
          company_id=company.id,
          forecast_date=today,
          target_date=target_dt,
          predicted_value=arima_forecast.iloc[i]
        )
        db.add(db_arima)
              
        db_garch = PredictionGarch(
          company_id=company.id,
          forecast_date=today,
          target_date=target_dt,
          predicted_volatility=garch_forecast.iloc[i]
        )
        db.add(db_garch)
      
    await db.commit()
  print(f"[{datetime.now()}] Nocny Job zakończony.")

def setup_scheduler():
  scheduler.add_job(run_nightly_prediction_job, 'cron', hour=1, minute=0)
  
  # Uruchom job raz teraz, do celów testowych (opcjonalne)
  # scheduler.add_job(run_nightly_prediction_job, 'date', run_date=datetime.now() + timedelta(seconds=10))
  
  scheduler.start()
  print("Scheduler uruchomiony.")