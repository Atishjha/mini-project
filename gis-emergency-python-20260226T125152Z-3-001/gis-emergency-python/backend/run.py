# backend/run.py
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 70)
    print("🚨 Emergency Response System with PostgreSQL + PostGIS")
    print("=" * 70)
    print("🔹 Database: PostgreSQL with PostGIS")
    print("🔹 Features: Incidents, Resources, Heatmaps, Analytics")
    print("\n🌐 Server: http://localhost:5432")
    print("=" * 70)
    
    with app.app_context():
        # Create tables if they don't exist
        from app.models.database import db
        db.create_all()
        print("✅ Database tables ready")
    
    app.run(debug=True, host='0.0.0.0', port=5432)