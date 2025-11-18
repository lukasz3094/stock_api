import pytest
import pytest_asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_predictions_unauthorized(client: AsyncClient):
  response = await client.get("/api/v1/predictions/BOS")
  assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_predictions_not_found(client: AsyncClient, logged_in_token: str):  
  headers = {"Authorization": f"Bearer {logged_in_token}"}
  response = await client.get("/api/v1/predictions/FAKE", headers=headers)
  assert response.status_code == 404
  assert response.json()["detail"] == "Company not found"

@pytest.mark.asyncio
async def test_get_predictions_no_data_yet(client: AsyncClient, logged_in_token: str):
  # (Zakładamy, że seeder w main.py dodał 'BOS' do bazy testowej,
  # ale Nocny Job nie dodał jeszcze prognoz)
  headers = {"Authorization": f"Bearer {logged_in_token}"}
  response = await client.get("/api/v1/predictions/BOS.WA", headers=headers)
  assert response.status_code == 404
  assert response.json()["detail"] == "No predictions found for this company yet."

@pytest.mark.asyncio
async def test_get_predictions_success(
  client: AsyncClient, logged_in_token: str, run_predictions
):
  headers = {"Authorization": f"Bearer {logged_in_token}"}
  
  response = await client.get("/api/v1/predictions/BOS.WA", headers=headers)
  
  assert response.status_code == 200
  data = response.json()
  
  assert data["ticker"] == "BOS.WA"
  assert "last_update" in data
  
  assert isinstance(data["arima_forecast"], list)
  assert isinstance(data["garch_forecast"], list)
  
  expected_days = 10
  assert len(data["arima_forecast"]) == expected_days
  assert len(data["garch_forecast"]) == expected_days
  
  arima_first = data["arima_forecast"][0]
  assert "target_date" in arima_first
  assert "predicted_value" in arima_first
  assert isinstance(arima_first["predicted_value"], (int, float))
  
  garch_first = data["garch_forecast"][0]
  assert "target_date" in garch_first
  assert "predicted_volatility" in garch_first
  assert isinstance(garch_first["predicted_volatility"], (int, float))
