# backend/app/__init__.py
from flask import Flask
from flask_cors import CORS
from app.utils.config import Config

# Don't import models here - create app first, then initialize
def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app)
    
    # Import and initialize db here to avoid circular imports
    from .models.database import db, init_db
    init_db(app)
    
    # Import and register routes after db is initialized
    from .main import register_routes
    register_routes(app)
    
    return app