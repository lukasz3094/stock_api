import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.pool import StaticPool
from unittest.mock import patch
from datetime import date, timedelta
import pandas as pd

from app.main import app
from app.db.base_class import Base
from app.models.company import Company
from app.models.price_history import PriceHistory
from app.models.prediction_arima import PredictionArima
from app.models.prediction_garch import PredictionGarch
from app.api.v1.endpoints_auth import get_db as get_db_auth
from app.api.deps import get_db as get_db_deps
from app.workers.scheduler import run_nightly_prediction_job
from app.core.security import get_password_hash

INITIAL_COMPANIES = [
    {"name": "Bank Ochrony Srodowiska S.A.", "ticker": "BOS.WA"},
    {"name": "Getin Holding SA", "ticker": "GTN.WA"},
    {"name": "Bank Handlowy w Warszawie S.A.", "ticker": "BHW.WA"},
    {"name": "Powszechna Kasa Oszczednosci Bank Polski Spólka Akcyjna", "ticker": "PKO.WA"},
    {"name": "Santander Bank Polska S.A.", "ticker": "SPL.WA"},
]

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

  SetupSession = async_sessionmaker(bind=engine, expire_on_commit=False)
  async with SetupSession() as db:
    for company_data in INITIAL_COMPANIES:
      result = await db.execute(select(Company).filter_by(ticker=company_data["ticker"]))
      if not result.scalar_one_or_none():
        db.add(Company(name=company_data["name"],
               ticker=company_data["ticker"]))
    await db.commit()

    # Add dummy PriceHistory, PredictionArima, and PredictionGarch for BOS.WA for tests
    bos_company = await db.execute(select(Company).filter_by(ticker="BOS.WA"))
    bos_company = bos_company.scalar_one()

    if bos_company:
      from datetime import date, timedelta

      today = date.today()
      # Add PriceHistory
      for i in range(1, 4):  # Add 3 days of history
        ph = PriceHistory(
            company_id=bos_company.id,
            date=today - timedelta(days=i),
            close=100.0 + i  # Dummy close price
        )
        db.add(ph)

      # Add PredictionArima
      for i in range(1, 11):  # 10 days of predictions
        pa = PredictionArima(
            company_id=bos_company.id,
            forecast_date=today,
            target_date=today + timedelta(days=i),
            predicted_value=105.0 + i
        )
        db.add(pa)

      # Add PredictionGarch
      for i in range(1, 11):  # 10 days of predictions
        pg = PredictionGarch(
            company_id=bos_company.id,
            forecast_date=today,
            target_date=today + timedelta(days=i),
            predicted_volatility=0.01 + i*0.001
        )
        db.add(pg)
      await db.commit()  # Commit the dummy data

  yield


@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_session():
  connection = await engine.connect()
  transaction = await connection.begin()

  session_factory = async_sessionmaker(
      bind=connection,
      expire_on_commit=False,
      class_=AsyncSession
  )

  shared_session = session_factory()
  shared_session.commit = shared_session.flush

  async def get_test_session():
    yield shared_session

  app.dependency_overrides[get_db_auth] = get_test_session
  app.dependency_overrides[get_db_deps] = get_test_session

  try:
    yield shared_session
  finally:
    await transaction.rollback()
    await shared_session.close()
    await connection.close()


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncClient:
  transport = ASGITransport(app=app)
  async with AsyncClient(transport=transport, base_url="http://test") as ac:
    yield ac


@pytest_asyncio.fixture(scope="function")
async def logged_in_token(client: AsyncClient) -> str:
  await client.post(
      "/api/v1/register",
      json={"email": "test-user@example.com", "password": "password123"},
  )

  response = await client.post(
      "/api/v1/login",
      data={"username": "test-user@example.com", "password": "password123"},
      headers={"Content-Type": "application/x-www-form-urlencoded"},
  )
  return response.json()["access_token"]


@pytest_asyncio.fixture(scope="function")
async def run_predictions(db_session):
  # run_nightly_prediction_job expects a list of tickers, and the test data is for BOS.WA
  await run_nightly_prediction_job(db=db_session, tickers=["BOS.WA"])
  yield
