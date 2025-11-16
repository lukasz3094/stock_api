from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings

DB_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DB_URL, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
  autocommit=False, autoflush=False, bind=engine
)