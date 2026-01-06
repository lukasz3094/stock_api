from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from app.config import Settings, settings
from app.api.v1 import endpoints_auth, endpoints_predictions, endpoints_companies, endpoints_interpret
from app.workers.scheduler import setup_scheduler, run_nightly_prediction_job
import app.db


@asynccontextmanager
async def lifespan(app: FastAPI):
  print("Uruchamianie: Start Nocnego Schedulera...")
  setup_scheduler()

  # Run the job once on startup in the background
  print("Uruchamianie jednorazowego zadania pobierania danych w tle...")
  asyncio.create_task(run_nightly_prediction_job())

  print("Startup zakończony.")

  yield

  print("Zamykanie aplikacji...")

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_settings() -> Settings:
  return settings


@app.get("/")
def read_root(settings: Settings = Depends(get_settings)):
  return {"message": f"Witaj w {settings.APP_NAME}"}


@app.get("/health")
def health_check():
  return {"status": "ok"}


app.include_router(endpoints_auth.router, prefix="/api/v1", tags=["Auth"])
app.include_router(endpoints_predictions.router,
                   prefix="/api/v1", tags=["Predictions"])
app.include_router(endpoints_companies.router,
                   prefix="/api/v1", tags=["Companies"])
app.include_router(endpoints_interpret.router,
                   prefix="/api/v1", tags=["Interpret"])
