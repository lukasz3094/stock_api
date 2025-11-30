from fastapi import APIRouter, Depends, HTTPException
from app.schemas.interpret import InterpretInput
from app.config import settings
import google.generativeai as genai

router = APIRouter()

@router.post("/predictions/interpret")
async def interpret_predictions(input_data: InterpretInput):
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured in the .env file. You can get a key from Google AI Studio.")

    if not input_data.arima_forecast or not input_data.garch_forecast:
        raise HTTPException(status_code=400, detail="ARIMA and GARCH forecast data are required.")

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    Przedstaw zwięzłą i profesjonalną analizę prognozy dla akcji, unikając języka typowego dla sztucznej inteligencji.
    Na podstawie danych o przewidywanej cenie i zmienności, sformułuj ocenę, czy prognoza jest stabilna/korzystna/niekorzystna.
    Jeżeli dane nie wskazują na znaczące zmiany w cenie lub zmienności, należy jasno określić brak wyraźnego trendu.
    Podsumowanie w formie komentarza rynkowego ma mieć DOKŁADNIE 2 zdania. Odpowiedź podaj w języku polskim.

    Prognoza cen (ARIMA, następne 10 dni): {', '.join([f'{p.predicted_value:.2f}' for p in input_data.arima_forecast])}
    Prognoza zmienności (GARCH, następne 10 dni): {', '.join([f'{p.predicted_volatility:.4f}' for p in input_data.garch_forecast])}
    """

    try:
        response = model.generate_content(prompt)
        return {"interpretation": response.text}
    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate interpretation: {e}")
