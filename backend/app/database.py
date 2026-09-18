from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# For SQLite fallback if Postgres is not running locally during development
db_url = settings.DATABASE_URL
import os
ENV_MODE = os.getenv("ENV", "development").lower()
IS_PROD = ENV_MODE == "production" or os.getenv("PRODUCTION", "False").lower() in ("true", "1", "yes")

if db_url.startswith("postgresql") and ("localhost" in db_url or "127.0.0.1" in db_url):
    # We can fallback to SQLite if PostgreSQL is not active locally and not in production
    if not os.getenv("FORCE_POSTGRES") and not IS_PROD:
        db_url = "sqlite:///./parkiq.db"

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
