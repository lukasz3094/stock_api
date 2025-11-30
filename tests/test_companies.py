import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_all_companies_unauthorized(client: AsyncClient):
  response = await client.get("/api/v1/companies")
  assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_all_companies_success(client: AsyncClient, logged_in_token: str):
  headers = {"Authorization": f"Bearer {logged_in_token}"}
  response = await client.get("/api/v1/companies", headers=headers)
  assert response.status_code == 200
  companies = response.json()
  assert isinstance(companies, list)
  assert len(companies) > 0
  for company in companies:
    assert "id" in company
    assert "name" in company
    assert "ticker" in company
    assert "current_price" in company
    assert "price_change" in company


@pytest.mark.asyncio
async def test_get_company_history_unauthorized(client: AsyncClient):
  response = await client.get("/api/v1/companies/BOS.WA/history")
  assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_company_history_not_found(client: AsyncClient, logged_in_token: str):
  headers = {"Authorization": f"Bearer {logged_in_token}"}
  response = await client.get("/api/v1/companies/NONEXISTENT/history", headers=headers)
  assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_company_history_success(client: AsyncClient, logged_in_token: str):
  headers = {"Authorization": f"Bearer {logged_in_token}"}
  response = await client.get("/api/v1/companies/BOS.WA/history", headers=headers)
  assert response.status_code == 200
  history = response.json()
  assert isinstance(history, list)
  # The actual length might vary based on when the data is seeded, but it should not be empty
  assert len(history) > 0
  if history:
    for entry in history:
      assert "date" in entry
      assert "close" in entry
