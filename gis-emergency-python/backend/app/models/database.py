# backend/app/models/database.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Create db instance - no imports from app
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with app"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully")