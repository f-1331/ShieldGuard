import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from backend.config import settings

logger = logging.getLogger("ShieldGuard.Database")

def get_engine_url_and_args(raw_url: str):
    """Baza URL manzilini moslashtiradi (Postgres asyncpg yoki SQLite)."""
    clean_url = (raw_url or "").strip()

    # Agar PostgreSQL bo'lsa (Neon yoki Render Postgres)
    if clean_url.startswith(("postgres://", "postgresql://", "postgresql+asyncpg://")):
        if clean_url.startswith("postgres://"):
            clean_url = clean_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif clean_url.startswith("postgresql://") and not clean_url.startswith("postgresql+asyncpg://"):
            clean_url = clean_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # asyncpg drayveri uchun sslmode=require o'rniga ssl=require
        if "sslmode=require" in clean_url:
            clean_url = clean_url.replace("sslmode=require", "ssl=require")

        return clean_url, {}

    # SQLite holati (Vercel serverless /tmp yoki mahalliy fayl)
    if os.environ.get("VERCEL") or not os.access(".", os.W_OK):
        clean_url = "sqlite+aiosqlite:////tmp/shieldguard.db"
    elif not clean_url:
        clean_url = "sqlite+aiosqlite:///./shieldguard.db"

    return clean_url, {"check_same_thread": False}

db_url, connect_args = get_engine_url_and_args(settings.DATABASE_URL)

engine = create_async_engine(
    db_url,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True
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
    logger.info("Ma'lumotlar bazasi jadvallari muvaffaqiyatli tekshirildi va ishga tushirildi.")
