import asyncio
from app.db.session import AsyncSessionLocal
from app.db import Company
from sqlalchemy import select

INITIAL_COMPANIES = [
    {"name": "Bank Ochrony Srodowiska S.A.", "ticker": "BOS.WA"},
    {"name": "Getin Holding SA", "ticker": "GTN.WA"},
    {"name": "Bank Handlowy w Warszawie S.A.", "ticker": "BHW.WA"},
    {"name": "Powszechna Kasa Oszczednosci Bank Polski Spólka Akcyjna", "ticker": "PKO.WA"},
    {"name": "Santander Bank Polska S.A.", "ticker": "SPL.WA"},
]


async def seed_companies():
  async with AsyncSessionLocal() as db:
    for company_data in INITIAL_COMPANIES:
      result = await db.execute(
          select(Company).filter_by(ticker=company_data["ticker"])
      )
      exists = result.scalar_one_or_none()
      if not exists:
        db_company = Company(
            name=company_data["name"],
            ticker=company_data["ticker"]
        )
        db.add(db_company)
        print(f"Dodano spółkę: {company_data['name']}")
    await db.commit()

if __name__ == "__main__":
  asyncio.run(seed_companies())
