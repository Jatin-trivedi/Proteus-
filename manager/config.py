import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# Load .env from manager directory or working directory
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "jocky_sih_2024_dev")
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        # Default to local SQLite database if PostgreSQL DATABASE_URL is not set
        default_db_path = os.path.join(BASE_DIR, "proteus.db")
        db_url = f"sqlite:///{default_db_path}"
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    DATABASE_URL = db_url
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXPIRATION = 3600  # seconds
    JWT_ALGORITHM = "HS256"
    
    CORS_ALLOWED_ORIGINS = tuple(
        origin.strip().rstrip("/")
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "https://jocky-snowy.vercel.app,https://jocky.netlify.app,http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080",
        ).split(",")
        if origin.strip().rstrip("/")
    )

    if db_url.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,       # Check connection before using
            "pool_recycle": 300,         # Recycle connections every 5 minutes
            "pool_size": 5,
            "max_overflow": 10,
        }