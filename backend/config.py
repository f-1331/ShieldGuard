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
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_BOT_USERNAME: str = os.getenv("TELEGRAM_BOT_USERNAME", "ShieldGuard_Pro_bot")
    TELEGRAM_APP_ID: str = os.getenv("TELEGRAM_APP_ID", "")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "https://shieldguard-five.vercel.app")

    # Super Owner (Faqat bitta yagona egasi)
    OWNER_TELEGRAM_ID: int = 6707839718
    OWNER_USERNAME: str = "fayzbek1331"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./shieldguard.db"

    def model_post_init(self, __context):
        if os.environ.get("VERCEL"):
            self.DATABASE_URL = "sqlite+aiosqlite:////tmp/shieldguard.db"
            if self.WEBAPP_URL == "http://localhost:8000" and os.environ.get("VERCEL_URL"):
                self.WEBAPP_URL = f"https://{os.environ.get('VERCEL_URL')}"

    # LLM Settings
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DEFAULT_LLM_PROVIDER: str = "gemini"

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()
