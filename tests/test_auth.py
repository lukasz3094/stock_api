import pytest
from httpx import AsyncClient

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
