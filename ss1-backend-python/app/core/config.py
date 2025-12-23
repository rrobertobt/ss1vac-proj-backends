from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    ENV: str = os.getenv("ENV", "local")
    PORT: int = int(os.getenv("PORT", "8001"))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    JWT_ACCESS_SECRET: str = os.getenv("JWT_ACCESS_SECRET", "change-me")
    JWT_ACCESS_EXPIRES_IN: str = os.getenv("JWT_ACCESS_EXPIRES_IN", "7d")

    JWT_2FA_SECRET: str = os.getenv("JWT_2FA_SECRET", "change-me-2fa")
    JWT_2FA_EXPIRES_IN: str = os.getenv("JWT_2FA_EXPIRES_IN", "10m")

    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "")

settings = Settings()
