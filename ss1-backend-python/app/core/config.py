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

    # Mail Mailtrap configuration
    MAILTRAP_API_TOKEN: str = os.getenv("MAILTRAP_TOKEN", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "PsiFirm")

settings = Settings()
