import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.models.company import Company
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
        db.add(Company(name=company_data["name"], ticker=company_data["ticker"]))
    await db.commit()

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
  await run_nightly_prediction_job(db=db_session, tickers=["BOS.WA"])
  yield
