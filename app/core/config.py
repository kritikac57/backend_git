# app/core/config.py
from pydantic import BaseSettings, PostgresDsn, EmailStr
import os
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "DonationApp"
    
    # CORS Configuration
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # Database Configuration
    DATABASE_USER: str = os.getenv("DATABASE_USER", "postgres")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "postgres")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: str = os.getenv("DATABASE_PORT", "5432")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "donationapp")
    
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @property
    def get_database_url(self) -> str:
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    # Email Configuration
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
    EMAIL_FROM: EmailStr = os.getenv("EMAIL_FROM", "noreply@donationapp.com")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.mailtrap.io")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "2525"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "True").lower() == "true"
    
    # Nominatim API Configuration
    NOMINATIM_USER_AGENT: str = "DonationApp/1.0"
    NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org"
    
    class Config:
        case_sensitive = True

settings = Settings()

# Set DATABASE_URL if not set explicitly
if settings.DATABASE_URL is None:
    settings.DATABASE_URL = settings.get_database_url