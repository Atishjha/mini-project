# backend/app/__init__.py
from flask import Flask
from flask_cors import CORS
from app.utils.config import Config

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)

    # Import and initialize db here to avoid circular imports
    from .models.database import init_db
    init_db(app)

    # Register blueprints AFTER app is created
    from app.routes import crowd
    app.register_blueprint(crowd.bp, url_prefix="/api/crowd")

    # If you have other routes registration
    # (make sure this does NOT import app.main in a way that imports create_app again)
    try:
        from .main import register_routes
        register_routes(app)
    except Exception:
        pass

    return app
