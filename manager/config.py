import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY= os.getenv("SECRET_KEY","jocky_sih_2024_dev")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///db/jocky.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXPIRATION = 3600  # seconds