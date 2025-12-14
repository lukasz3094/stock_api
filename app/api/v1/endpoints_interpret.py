from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.prediction_arima import PredictionArima
from app.models.prediction_garch import PredictionGarch
from app.models.prediction_lstm import PredictionLstm
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
    model_names: List[str] = Query(..., enum=["arima", "lstm"]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    price_history_result = await db.execute(select(PriceHistory).join(Company).filter(Company.ticker == symbol.upper()).filter(PriceHistory.date >= start_date).order_by(PriceHistory.date.asc()))
    price_history = price_history_result.scalars().fetchall()

    prompt_parts = [
        "Jesteś analitykiem finansowym. Twoim zadaniem jest ocena prognozy giełdowej dla klienta.",
        "Na podstawie dostarczonych danych, stwórz krótką, zwięzłą analizę w jednym, maksymalnie dwóch zdaniach po polsku.",
        "Skup się na ogólnym trendzie i stabilności, unikając technicznego żargonu.",
        "Pamiętaj, że prognoza zmienności (GARCH) jest uzupełnieniem prognozy cen (ARIMA) i odnosi się do tego samego modelu.",
        "\nDane:",
        f"Historyczne ceny zamknięcia (ostatnie 30 dni): {', '.join([f'{p.close:.2f}' for p in price_history])}"
    ]
    
    data_found = False
    
    if "arima" in model_names:
        arima_result = await db.execute(select(PredictionArima).join(Company).filter(Company.ticker == symbol.upper()).order_by(PredictionArima.target_date.desc()).limit(10))
        arima_forecasts = arima_result.scalars().fetchall()
        if arima_forecasts:
            data_found = True
            arima_forecasts.reverse()
            prompt_parts.append(f"Prognoza cen (ARIMA): {', '.join([f'{p.predicted_value:.2f}' for p in arima_forecasts])}")
            
        garch_result = await db.execute(select(PredictionGarch).join(Company).filter(Company.ticker == symbol.upper()).order_by(PredictionGarch.target_date.desc()).limit(10))
        garch_forecasts = garch_result.scalars().fetchall()
        if garch_forecasts:
            data_found = True
            garch_forecasts.reverse()
            prompt_parts.append(f"Prognoza zmienności (GARCH): {', '.join([f'{p.predicted_volatility:.4f}' for p in garch_forecasts])}")

    if "lstm" in model_names:
        lstm_result = await db.execute(select(PredictionLstm).join(Company).filter(Company.ticker == symbol.upper()).order_by(PredictionLstm.target_date.desc()).limit(10))
        lstm_forecasts = lstm_result.scalars().fetchall()
        if lstm_forecasts:
            data_found = True
            lstm_forecasts.reverse()
            prompt_parts.append(f"Prognoza cen (LSTM): {', '.join([f'{p.predicted_value:.2f}' for p in lstm_forecasts])}")

    if not data_found:
        raise HTTPException(
            status_code=404, detail=f"No prediction data found for symbol: {symbol} and selected models.")

    prompt = "\n".join(prompt_parts)

    return StreamingResponse(stream_interpretation(prompt), media_type="text/event-stream")
