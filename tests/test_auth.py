import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.db.base import Base
from app.api.v1.endpoints_auth import get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
  TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def override_get_db():
  async with TestingSessionLocal() as session:
    yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_db():
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
  yield
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="module")
async def client() -> AsyncClient: 
  transport = ASGITransport(app=app)
  async with AsyncClient(transport=transport, base_url="http://test") as ac:
      yield ac

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
  response = await client.post(
    "/api/v1/register", 
    json={"email": "test@example.com", "password": "password123"},
  )
  assert response.status_code == 200
  data = response.json()
  assert data["email"] == "test@example.com"
  assert "id" in data
  assert "hashed_password" not in data

@pytest.mark.asyncio
async def test_register_existing_user(client: AsyncClient):
  await client.post(
    "/api/v1/register", 
    json={"email": "test2@example.com", "password": "password123"},
  )
  response = await client.post(
    "/api/v1/register",
    json={"email": "test2@example.com", "password": "password123"},
  )
  assert response.status_code == 400
  assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_for_access_token(client: AsyncClient):
  await client.post(
    "/api/v1/register", 
    json={"email": "login@example.com", "password": "password123"},
  )
  
  response = await client.post(
    "/api/v1/login",
    data={"username": "login@example.com", "password": "password123"},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
  )
  assert response.status_code == 200
  data = response.json()
  assert "access_token" in data
  assert data["token_type"] == "bearer"
