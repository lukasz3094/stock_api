import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.future import select

from app.main import app
from app.db.base import Base

from app.models.user import User
from app.models.company import Company
from app.models.predictions import PredictionArima, PredictionGarch

from app.api.v1.endpoints_auth import get_db as get_db_auth
from app.api.deps import get_db as get_db_deps

INITIAL_COMPANIES = [
  {"name": "Bank Ochrony Srodowiska S.A.", "ticker": "BOS.WA"},
  {"name": "Getin Holding SA", "ticker": "GTN.WA"},
  {"name": "Bank Handlowy w Warszawie S.A.", "ticker": "BHW.WA"},
  {"name": "Powszechna Kasa Oszczednosci Bank Polski Spólka Akcyjna", "ticker": "PKO.WA"},
  {"name": "Santander Bank Polska S.A.", "ticker": "SPL.WA"},
]

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
  TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def override_get_db():
  async with TestingSessionLocal() as session:
    yield session

app.dependency_overrides[get_db_auth] = override_get_db
app.dependency_overrides[get_db_deps] = override_get_db

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
    
  async with TestingSessionLocal() as db:
    for company_data in INITIAL_COMPANIES:  
      result = await db.execute(
        select(Company).filter_by(ticker=company_data["ticker"])
      )
      existing = result.scalar_one_or_none()

      if not existing:
        db_company = Company(
          name=company_data["name"], 
          ticker=company_data["ticker"]
        )
        db.add(db_company)
        
    await db.commit()
    
  yield
    
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncClient:
  transport = ASGITransport(app=app)
  async with AsyncClient(transport=transport, base_url="http://test") as ac:
    yield ac

@pytest_asyncio.fixture(scope="module")
async def logged_in_token(client: AsyncClient) -> str:
  await client.post(
    "/api/v1/register",
    json={"email": "test-user-for-token@example.com", "password": "password123"},
  )
   
  response = await client.post(
    "/api/v1/login",
    data={"username": "test-user-for-token@example.com", "password": "password123"},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
  )
  return response.json()["access_token"]
