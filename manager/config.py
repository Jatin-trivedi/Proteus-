import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY= os.getenv("SECRET_KEY","jocky_sih_2024_dev")
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL must be configured for PostgreSQL")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXPIRATION = 3600  # seconds
    JWT_ALGORITHM = "HS256"
    CORS_ALLOWED_ORIGINS = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:3000",
        ).split(",")
        if origin.strip()
    )

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,       # Check connection before using
        "pool_recycle": 300,         # Recycle connections every 5 minutes
        "pool_size": 10,
        "max_overflow": 20
    }