import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "ParkIQ AI Prediction Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1/ai"
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # Database URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://parkiq:parkiq_pass@localhost:5432/parkiq_db")
    
    # Model Directory for saved weights
    MODEL_DIR: str = os.getenv("MODEL_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml", "saved_models"))

    @property
    def final_database_url(self) -> str:
        # Fallback to local SQLite if Postgres is on localhost and not forced and not production
        url = self.DATABASE_URL
        ENV_MODE = os.getenv("ENV", "development").lower()
        IS_PROD = ENV_MODE == "production" or os.getenv("PRODUCTION", "False").lower() in ("true", "1", "yes")
        
        if url.startswith("postgresql") and ("localhost" in url or "127.0.0.1" in url):
            if not os.getenv("FORCE_POSTGRES") and not IS_PROD:
                # Try to locate the SQLite DB relative to the workspace
                # If running locally from c:\ParkIQ, backend/parkiq.db is the path
                possible_paths = [
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "parkiq.db")),
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "parkiq.db")),
                    "./parkiq.db"
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        return f"sqlite:///{path}"
                return "sqlite:///./parkiq.db"
        return url

    class Config:
        case_sensitive = True

settings = Settings()
