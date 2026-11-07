import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from backend.config import settings

# Ensure sqlite directory exists if local file path
database_url = settings.DATABASE_URL
if os.environ.get("VERCEL") or not os.access(".", os.W_OK):
    database_url = "sqlite+aiosqlite:////tmp/shieldguard.db"
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_async_engine(
    database_url,
    echo=False,
    connect_args=connect_args
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        from backend import models  # import to register models with Base
        await conn.run_sync(Base.metadata.create_all)
