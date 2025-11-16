from fastapi import FastAPI, Depends
from .config import Settings, settings

app = FastAPI(title=settings.APP_NAME)

def get_settings() -> Settings:
  return settings

@app.get("/")
def read_root(settings: Settings = Depends(get_settings)):
  """ Główny endpoint, który pokazuje nazwę aplikacji z konfiguracji. """
  return {"message": f"Witaj w {settings.APP_NAME}"}

@app.get("/health")
def health_check():
  return {"status": "ok"}