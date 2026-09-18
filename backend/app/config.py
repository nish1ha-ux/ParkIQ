import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "ParkIQ Smart Parking Intelligence Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # Security & Encryption
    SECRET_KEY: str = os.getenv("SECRET_KEY", "parkiq_super_secret_jwt_key_2026_enterprise_987654321")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))  # Default 60 minutes (1 hour)
    
    # AES-256 Secret Key for QR Code encryption (Must be 32 bytes hex encoded or string)
    AES_QR_SECRET_KEY: str = os.getenv("AES_QR_SECRET_KEY", "0123456789abcdef0123456789abcdef")  # 32 chars
    QR_VALIDITY_WINDOW_SECONDS: int = int(os.getenv("QR_VALIDITY_WINDOW_SECONDS", 300))  # 5 minutes
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://parkiq:parkiq_pass@localhost:5432/parkiq_db")
    
    # Redis Cache & WebSockets
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    
    # AI & RAG
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", "./chroma_data")
    AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
    
    # Razorpay Payment Gateway
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_parkiq_key")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "rzp_test_parkiq_secret")
    
    # Firebase Cloud Messaging
    FIREBASE_CREDENTIALS_PATH: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_PATH", None)
    FCM_MOCK_MODE: bool = os.getenv("FCM_MOCK_MODE", "True").lower() in ("true", "1", "yes")

    class Config:
        case_sensitive = True

settings = Settings()

# Production Hardening Checks
import sys
ENV_MODE = os.getenv("ENV", "development").lower()
IS_PROD = ENV_MODE == "production" or os.getenv("PRODUCTION", "False").lower() in ("true", "1", "yes")

if IS_PROD:
    errors = []
    if settings.SECRET_KEY == "parkiq_super_secret_jwt_key_2026_enterprise_987654321":
        errors.append("SECRET_KEY must be changed from the default value in production.")
    if settings.AES_QR_SECRET_KEY == "0123456789abcdef0123456789abcdef":
        errors.append("AES_QR_SECRET_KEY must be changed from the default value in production.")
    if "parkiq_pass" in settings.DATABASE_URL:
        errors.append("DATABASE_URL must not use default local database password in production.")
    if settings.RAZORPAY_KEY_SECRET == "rzp_test_parkiq_secret":
        errors.append("RAZORPAY_KEY_SECRET must be changed from the default value in production.")
    
    if errors:
        print("\n[FATAL] Production Hardening Validation Failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

