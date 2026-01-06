import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_interpret_predictions_unauthorized(client: AsyncClient):
  response = await client.get("/api/v1/interpret/BOS.WA")
  assert response.status_code == 401


@pytest.mark.asyncio
async def test_interpret_predictions_not_found(client: AsyncClient, logged_in_token: str):
  headers = {"Authorization": f"Bearer {logged_in_token}"}
  response = await client.get("/api/v1/interpret/NONEXISTENT", headers=headers)
  assert response.status_code == 404
  assert response.json()[
      "detail"] == "No prediction data found for symbol: NONEXISTENT"


@pytest.mark.asyncio
async def test_interpret_predictions_success(client: AsyncClient, logged_in_token: str):
  headers = {"Authorization": f"Bearer {logged_in_token}"}

  mock_text_chunks = ["Mocked interpretation part 1. ",
                      "Mocked interpretation part 2."]

  with patch("app.api.v1.endpoints_interpret.stream_interpretation") as mock_stream_interpretation:
    async def mock_generator():
      for chunk in mock_text_chunks:
        yield chunk
    mock_stream_interpretation.return_value = mock_generator()

    response = await client.get("/api/v1/interpret/BOS.WA", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Read the streaming response content
    content = ""
    async for chunk in response.aiter_bytes():
      content += chunk.decode("utf-8")

    expected_content = "".join(mock_text_chunks)
    assert expected_content in content
    mock_stream_interpretation.assert_called_once()
