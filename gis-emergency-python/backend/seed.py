# backend/seed.py
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.database import db
from app.models.incidents import Incident
from app.models.resource import Resource, ResourceAllocation
from app.models.user import CallerHistory
from app.models.crowd import CrowdLocation, CrowdData
from datetime import datetime, timedelta
import random

def seed_database():
    """Seed the database with sample data"""
    app = create_app()
    
    with app.app_context():
        print("🗑️  Dropping existing tables...")
        db.drop_all()
        
        print("🏗️  Creating tables...")
        db.create_all()
        
        print("🌱 Seeding database with sample data...")
        
        # Sample incidents
        locations = [
            (28.6139, 77.2090, "Connaught Place, Delhi"),
            (28.6239, 77.2190, "Preet Vihar, Delhi"),
            (28.6339, 77.2290, "Rohini, Delhi"),
            (28.6039, 77.1990, "Saket, Delhi"),
            (28.5939, 77.1890, "Dwarka, Delhi")
        ]
        
        types = ['fire', 'medical', 'accident', 'flood', 'earthquake']
        caller_types = ['verified', 'first_time', 'anonymous', 'emergency_services']
        statuses = ['active', 'resolved', 'active']
        
        incidents_created = 0
        for i in range(20):
            lat, lng, addr = random.choice(locations)
            lat += random.uniform(-0.02, 0.02)
            lng += random.uniform(-0.02, 0.02)
            
            incident_type = random.choice(types)
            severity_score = random.uniform(3, 9.5)
            
            # Use text function for PostGIS
            from sqlalchemy import text
            point = text(f'ST_GeomFromText(:wkt, 4326)')
            wkt = f'POINT({lng} {lat})'
            
            incident = Incident(
                incident_type=incident_type,
                severity=int(severity_score / 2),
                severity_score=severity_score,
                prank_confidence=random.uniform(0.05, 0.8),
                verified=random.random() > 0.3,
                address=addr,
                description=f"{incident_type.capitalize()} incident at {addr}",
                reported_at=datetime.now() - timedelta(hours=random.randint(1, 48)),
                status=random.choice(statuses),
                caller_id=f"caller_{random.randint(1000, 9999)}",
                caller_type=random.choice(caller_types),
                location_type=random.choice(['residential', 'commercial', 'public']),
                call_count=random.randint(1, 5)
            )
            
            # Set location using raw SQL
            incident.location = db.session.execute(
                text(f"SELECT ST_GeomFromText('{wkt}', 4326)")
            ).scalar()
            
            db.session.add(incident)
            incidents_created += 1
        
        # Sample resources
        resource_types = ['ambulance', 'fire_truck', 'police']
        
        resources_created = 0
        for i in range(15):
            lat, lng, addr = random.choice(locations)
            lat += random.uniform(-0.03, 0.03)
            lng += random.uniform(-0.03, 0.03)
            
            wkt = f'POINT({lng} {lat})'
            resource_type = random.choice(resource_types)
            
            resource = Resource(
                resource_type=resource_type,
                status=random.choice(['available', 'dispatched']),
                capacity=random.randint(2, 6),
                details={'equipment': ['standard']},
                last_update=datetime.now() - timedelta(minutes=random.randint(5, 60))
            )
            
            # Set location using raw SQL
            resource.location = db.session.execute(
                text(f"SELECT ST_GeomFromText('{wkt}', 4326)")
            ).scalar()
            
            db.session.add(resource)
            resources_created += 1
        
        # Sample caller history
        callers_created = 0
        for i in range(10):
            caller_id = f"caller_{random.randint(1000, 9999)}"
            total = random.randint(1, 15)
            false_reports = random.randint(0, int(total * 0.3))
            
            history = CallerHistory(
                caller_id=caller_id,
                caller_type=random.choice(caller_types),
                total_reports=total,
                false_reports=false_reports,
                last_report=datetime.now() - timedelta(days=random.randint(1, 15)),
                reputation_score=1.0 - (false_reports / total if total > 0 else 0.5)
            )
            db.session.add(history)
            callers_created += 1
        
        # Commit all changes
        db.session.commit()
        
        print("\n" + "="*50)
        print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"📊 Created: {incidents_created} incidents")
        print(f"📊 Created: {resources_created} resources")
        print(f"📊 Created: {callers_created} caller histories")
        
        # Verify counts
        print(f"\n🔍 Verification:")
        print(f"   - Incidents in database: {Incident.query.count()}")
        print(f"   - Resources in database: {Resource.query.count()}")
        print(f"   - Caller histories: {CallerHistory.query.count()}")

if __name__ == "__main__":
    seed_database()