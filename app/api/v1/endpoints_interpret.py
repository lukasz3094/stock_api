from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.prediction_arima import PredictionArima
from app.models.prediction_garch import PredictionGarch
from app.models.price_history import PriceHistory
from app.models.company import Company
from app.models.user import User
from app.config import settings
import google.generativeai as genai
from typing import List
from fastapi.responses import StreamingResponse
from datetime import date, timedelta


router = APIRouter()


def stream_interpretation(prompt: str):
  if not settings.GEMINI_API_KEY:
    raise HTTPException(
        status_code=500, detail="GEMINI_API_KEY is not configured in the .env file. You can get a key from Google AI Studio.")

  try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt, stream=True)
    for chunk in response:
      yield chunk.text
  except Exception as e:
    print(f"Error during Gemini API call: {e}")
    yield f"Failed to generate interpretation: {e}"


@router.get("/interpret/{symbol}")
async def interpret_predictions(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
  end_date = date.today()
  start_date = end_date - timedelta(days=30)
  
  arima_result = await db.execute(select(PredictionArima).join(Company).filter(Company.ticker == symbol.upper()).order_by(PredictionArima.target_date.desc()).limit(10))
  garch_result = await db.execute(select(PredictionGarch).join(Company).filter(Company.ticker == symbol.upper()).order_by(PredictionGarch.target_date.desc()).limit(10))
  price_history_result = await db.execute(select(PriceHistory).join(Company).filter(Company.ticker == symbol.upper()).filter(PriceHistory.date >= start_date).order_by(PriceHistory.date.asc()))

  arima_forecasts = arima_result.scalars().fetchall()
  garch_forecasts = garch_result.scalars().fetchall()
  price_history = price_history_result.scalars().fetchall()

  if not arima_forecasts or not garch_forecasts:
    raise HTTPException(
        status_code=404, detail=f"No prediction data found for symbol: {symbol}")

  arima_forecasts.reverse()
  garch_forecasts.reverse()

  prompt = f"""
    Jesteś analitykiem finansowym. Twoim zadaniem jest ocena prognozy giełdowej dla klienta w jednym zdaniu po polsku.
    Biorąc pod uwagę historyczne ceny, prognozę cen ARIMA i prognozę zmienności GARCH, podsumuj prognozę.
    Skup się na stabilności i ogólnym trendzie. Unikaj technicznego żargonu.

    Dane:
    Historyczne ceny zamknięcia (ostatnie 30 dni): {', '.join([f'{p.close:.2f}' for p in price_history])}
    Prognoza cen (ARIMA): {', '.join([f'{p.predicted_value:.2f}' for p in arima_forecasts])}
    Prognoza zmienności (GARCH): {', '.join([f'{p.predicted_volatility:.4f}' for p in garch_forecasts])}
    """

  return StreamingResponse(stream_interpretation(prompt), media_type="text/event-stream")
