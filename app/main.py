from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from app.config import Settings, settings
from app.db.base import Base
from app.db.session import engine, AsyncSessionLocal
from app.api.v1 import endpoints_auth, endpoints_predictions
from app.workers.scheduler import setup_scheduler

from app.models.company import Company
from sqlalchemy.future import select

INITIAL_COMPANIES = [
  {"name": "Bank Ochrony Srodowiska S.A.", "ticker": "BOS.WA"},
  {"name": "Getin Holding SA", "ticker": "GTN.WA"},
  {"name": "Bank Handlowy w Warszawie S.A.", "ticker": "BHW.WA"},
  {"name": "Powszechna Kasa Oszczednosci Bank Polski Spólka Akcyjna", "ticker": "PKO.WA"},
  {"name": "Santander Bank Polska S.A.", "ticker": "SPL.WA"},
]

async def seed_companies():
  async with AsyncSessionLocal() as db:
    for company_data in INITIAL_COMPANIES:
      result = await db.execute(
        select(Company).filter_by(ticker=company_data["ticker"])
      )
      exists = result.scalar_one_or_none()
      if not exists:
        db_company = Company(
          name=company_data["name"], 
          ticker=company_data["ticker"]
        )
        db.add(db_company)
        print(f"Dodano spółkę: {company_data['name']}")
    await db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):  
  print("Uruchamianie: Tworzenie tabel w bazie danych...")
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

  print("Uruchamianie: Dodawanie spółek (seeding)...")
  await seed_companies()

  print("Uruchamianie: Start Nocnego Schedulera...")
  setup_scheduler()

  print("Startup zakończony.")
    
  yield
    
  print("Zamykanie aplikacji...")

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

def get_settings() -> Settings:
  return settings

@app.get("/")
def read_root(settings: Settings = Depends(get_settings)):
  return {"message": f"Witaj w {settings.APP_NAME}"}

@app.get("/health")
def health_check():
  return {"status": "ok"}

app.include_router(endpoints_auth.router, prefix="/api/v1", tags=["Auth"])
app.include_router(endpoints_predictions.router, prefix="/api/v1", tags=["Predictions"])
