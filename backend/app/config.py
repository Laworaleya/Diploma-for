import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017/financial_literacy"
    MONGODB_DB_NAME: str = "financial_literacy"

    # Redis
    REDIS_URI: str = ""

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_PROMPT_ID: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini"
    OPENAI_API_TIMEOUT_SECONDS: int = 45

    # JWT
    JWT_SECRET: str = "dev-jwt-secret-key-2026-finlit"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = ""

    # App
    APP_NAME: str = "FinLit Platform"
    APP_VERSION: str = "1.0.0"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    class Config:
        # Look for .env in backend/ dir first, then project root
        env_file = (
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        )
        env_file_encoding = "utf-8"


settings = Settings()
