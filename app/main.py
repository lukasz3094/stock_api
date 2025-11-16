# app/main.py

from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from app.config import Settings, settings
from app.db.base import Base
from app.db.session import engine
from app.api.v1 import endpoints_auth

@asynccontextmanager
async def lifespan(app: FastAPI):  
  print("Uruchamianie: Tworzenie tabel w bazie danych...")
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
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