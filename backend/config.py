import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "ShieldGuard AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "9237470345:AAFP4NeaViJGQOHPCGoMPvGZKkLY4lImtYI")
    TELEGRAM_BOT_USERNAME: str = os.getenv("TELEGRAM_BOT_USERNAME", "ShieldGuard_Pro_bot")
    TELEGRAM_APP_ID: str = os.getenv("TELEGRAM_APP_ID", "app9237470345:rq7oPX1N4rcAMvfLCNj8_VfSiXhkcTGZV0SJJ5rjrYU")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "https://shieldguardpro.vercel.app")

    # Super Owner (Faqat bitta yagona egasi)
    OWNER_TELEGRAM_ID: int = int(os.getenv("OWNER_TELEGRAM_ID", "6707839718"))
    OWNER_USERNAME: str = os.getenv("OWNER_USERNAME", "fayzbek1331")

    # Database: Doimiy Bulutli PostgreSQL (Neon DB)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://neondb_owner:npg_qYPjkF5DplJ4@ep-cold-credit-bekmk1wt-pooler.c-9.us-east-2.aws.neon.tech/neondb?sslmode=require"
    )

    def model_post_init(self, __context):
        if os.environ.get("VERCEL"):
            # Agar DATABASE_URL ko'rsatilmagan yoki sqlite bo'lsa, /tmp ga o'tadi
            if not self.DATABASE_URL or self.DATABASE_URL.startswith("sqlite"):
                if "tmp" not in self.DATABASE_URL:
                    self.DATABASE_URL = "sqlite+aiosqlite:////tmp/shieldguard.db"
            if self.WEBAPP_URL == "http://localhost:8000" and os.environ.get("VERCEL_URL"):
                self.WEBAPP_URL = f"https://{os.environ.get('VERCEL_URL')}"

    # LLM Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
