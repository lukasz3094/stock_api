from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

DB_URL = settings.DATABASE_URL

if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DB_URL and DB_URL.startswith("postgresql://"):
     DB_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

if "?sslmode=" in DB_URL:
    DB_URL = DB_URL.split("?sslmode=")[0]
if "&sslmode=" in DB_URL:
    import re
    DB_URL = re.sub(r"&sslmode=[^&]+", "", DB_URL)

engine = create_async_engine(
    DB_URL, 
    echo=True,
    connect_args={"ssl": "require"} # Force SSL for Neon
)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
