import asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.prediction_arima import PredictionArima
from app.models.prediction_garch import PredictionGarch
from app.models.prediction_lstm import PredictionLstm

async def clear_predictions(db: AsyncSession):
    """
    Deletes all predictions from the database.
    """
    await db.execute(delete(PredictionArima))
    await db.execute(delete(PredictionGarch))
    await db.execute(delete(PredictionLstm))
    await db.commit()

async def main():
    print("Clearing all predictions...")
    async with AsyncSessionLocal() as session:
        await clear_predictions(session)
    print("All predictions have been cleared.")

if __name__ == "__main__":
    asyncio.run(main())
