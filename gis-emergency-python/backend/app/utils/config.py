# backend/app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 
        'postgresql://postgres:1234567890@localhost:5432/emergency_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
    USGS_API_KEY = os.getenv('USGS_API_KEY')
    
    # SRID for spatial data
    SRID = 4326