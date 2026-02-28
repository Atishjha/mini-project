# backend/seed.py

import sys
import os
import random
from datetime import datetime, timedelta

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.database import db
from app.models.incidents import Incident
from app.models.resource import Resource
from app.models.user import CallerHistory
from geoalchemy2.elements import WKTElement


# =========================
# CROWD DETECTION MODEL
# =========================

from app.models.database import db
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON

class CrowdDetection(db.Model):
    """Model to store crowd detection events at various locations"""
    __tablename__ = 'crowd_detections'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Location info
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    address = Column(String(255), nullable=True)
    place_type = Column(String(100), nullable=True)   # open_field, market, park, stadium, street, etc.

    # Crowd metrics
    estimated_crowd_size = Column(Integer, nullable=False)          # Estimated number of people
    crowd_density = Column(String(50), nullable=False)              # low / moderate / high / critical
    density_score = Column(Float, nullable=False)                   # 0.0 - 1.0 (normalized density)

    # Detection metadata
    detection_source = Column(String(100), nullable=True)           # camera / satellite / sensor / manual / drone
    detection_confidence = Column(Float, nullable=False)            # 0.0 - 1.0
    is_anomalous = Column(Boolean, default=False)                   # Unusual crowd for that location/time
    risk_level = Column(String(50), nullable=True)                  # safe / moderate / high / critical

    # Temporal info
    detected_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Extra metadata (e.g., event name, weather, camera_id)
    extra_metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return (
            f"<CrowdDetection id={self.id} place='{self.address}' "
            f"size={self.estimated_crowd_size} density='{self.crowd_density}' "
            f"risk='{self.risk_level}'>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "address": self.address,
            "place_type": self.place_type,
            "estimated_crowd_size": self.estimated_crowd_size,
            "crowd_density": self.crowd_density,
            "density_score": round(self.density_score, 3),
            "detection_source": self.detection_source,
            "detection_confidence": round(self.detection_confidence, 3),
            "is_anomalous": self.is_anomalous,
            "risk_level": self.risk_level,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "extra_metadata": self.extra_metadata,
        }


# =========================
# CROWD DETECTION UTILITY
# =========================

def classify_crowd(crowd_size: int, area_sqm: float = 500.0):
    """
    Classify crowd density and risk level based on crowd size and area.

    Args:
        crowd_size: Estimated number of people
        area_sqm:   Approximate area in square meters (default 500 sqm)

    Returns:
        dict with density label, density_score, and risk_level
    """
    people_per_sqm = crowd_size / area_sqm

    if people_per_sqm < 0.5:
        density = "low"
        density_score = people_per_sqm / 0.5
        risk = "safe"
    elif people_per_sqm < 1.5:
        density = "moderate"
        density_score = 0.3 + (people_per_sqm - 0.5) / 1.0 * 0.3
        risk = "moderate"
    elif people_per_sqm < 3.0:
        density = "high"
        density_score = 0.6 + (people_per_sqm - 1.5) / 1.5 * 0.3
        risk = "high"
    else:
        density = "critical"
        density_score = min(1.0, 0.9 + (people_per_sqm - 3.0) / 3.0 * 0.1)
        risk = "critical"

    return {
        "crowd_density": density,
        "density_score": round(min(density_score, 1.0), 4),
        "risk_level": risk,
    }


def detect_crowds_at_location(lat: float, lng: float, address: str, place_type: str):
    """
    Simulate crowd detection at a given location.
    In production, replace this function body with actual detection logic,
    e.g., calling a computer-vision model, satellite imagery API, or IoT sensors.

    Args:
        lat, lng:    Geographic coordinates
        address:     Human-readable address
        place_type:  Type of location (open_field, park, market, etc.)

    Returns:
        CrowdDetection ORM object (not yet committed to DB)
    """
    # --- Simulated detection (replace with real model/API in production) ---
    crowd_size = random.randint(10, 5000)

    # Area estimation based on place type (rough approximation in sqm)
    area_map = {
        "open_field": 10000,
        "park": 5000,
        "market": 2000,
        "stadium": 50000,
        "street": 800,
        "commercial": 1500,
        "religious_site": 3000,
        "transport_hub": 4000,
    }
    area_sqm = area_map.get(place_type, 1000)

    classification = classify_crowd(crowd_size, area_sqm)

    detection_sources = ["camera", "satellite", "sensor", "manual", "drone"]
    source = random.choice(detection_sources)
    confidence = round(random.uniform(0.60, 0.99), 3)

    # Flag as anomalous if density is high/critical during non-peak hours
    hour = datetime.utcnow().hour
    is_peak_hour = 8 <= hour <= 21
    is_anomalous = (classification["crowd_density"] in ("high", "critical")) and not is_peak_hour

    detection = CrowdDetection(
        location=WKTElement(f'POINT({lng} {lat})', srid=4326),
        address=address,
        place_type=place_type,
        estimated_crowd_size=crowd_size,
        crowd_density=classification["crowd_density"],
        density_score=classification["density_score"],
        detection_source=source,
        detection_confidence=confidence,
        is_anomalous=is_anomalous,
        risk_level=classification["risk_level"],
        detected_at=datetime.utcnow() - timedelta(minutes=random.randint(0, 120)),
        extra_metadata={
            "area_sqm": area_sqm,
            "source_device_id": f"{source}_{random.randint(100, 999)}",
            "weather": random.choice(["clear", "cloudy", "rainy", "sunny"]),
            "event": random.choice([None, None, "festival", "protest", "sports_event", "concert"]),
        }
    )

    return detection


# =========================
# MAIN SEED FUNCTION
# =========================

def seed_database():
    """Seed the database with sample data"""

    app = create_app()

    with app.app_context():
        print("🗑️  Dropping existing tables...")
        db.drop_all()

        print("🏗️  Creating tables...")
        db.create_all()

        print("🌱 Seeding database with sample data...")

        # -----------------------------
        # Sample Locations (Delhi area)
        # -----------------------------
        locations = [
            (28.6139, 77.2090, "Connaught Place, Delhi"),
            (28.6239, 77.2190, "Preet Vihar, Delhi"),
            (28.6339, 77.2290, "Rohini, Delhi"),
            (28.6039, 77.1990, "Saket, Delhi"),
            (28.5939, 77.1890, "Dwarka, Delhi")
        ]

        types = ['fire', 'medical', 'accident', 'flood', 'earthquake']
        caller_types = ['verified', 'first_time', 'anonymous', 'emergency_services']
        statuses = ['active', 'resolved']

        # =========================
        # INCIDENTS
        # =========================
        incidents_created = 0

        for _ in range(20):
            lat, lng, addr = random.choice(locations)
            lat += random.uniform(-0.02, 0.02)
            lng += random.uniform(-0.02, 0.02)

            incident_type = random.choice(types)
            severity_score = random.uniform(3, 9.5)

            incident = Incident(
                incident_type=incident_type,
                severity=int(severity_score / 2),
                prank_confidence=random.uniform(0.05, 0.8),
                verified=random.random() > 0.3,
                address=addr,
                description=f"{incident_type.capitalize()} incident at {addr}",
                reported_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
                status=random.choice(statuses),
                caller_id=f"caller_{random.randint(1000, 9999)}",
                caller_type=random.choice(caller_types),
                location_type=random.choice(['residential', 'commercial', 'public']),
                call_count=random.randint(1, 5),
                location=WKTElement(f'POINT({lng} {lat})', srid=4326)
            )

            db.session.add(incident)
            incidents_created += 1

        # =========================
        # RESOURCES
        # =========================
        resource_types = ['ambulance', 'fire_truck', 'police']
        resources_created = 0

        for _ in range(15):
            lat, lng, _ = random.choice(locations)
            lat += random.uniform(-0.03, 0.03)
            lng += random.uniform(-0.03, 0.03)

            resource = Resource(
                resource_type=random.choice(resource_types),
                current_location=WKTElement(f'POINT({lng} {lat})', srid=4326),
                status=random.choice(['available', 'dispatched']),
                capacity=random.randint(2, 6),
                details={'equipment': ['standard']},
                last_update=datetime.utcnow() - timedelta(minutes=random.randint(5, 60))
            )

            db.session.add(resource)
            resources_created += 1

        # =========================
        # CALLER HISTORY
        # =========================
        callers_created = 0

        for _ in range(10):
            caller_id = f"caller_{random.randint(1000, 9999)}"
            total = random.randint(1, 15)
            false_reports = random.randint(0, int(total * 0.3))

            history = CallerHistory(
                caller_id=caller_id,
                caller_type=random.choice(caller_types),
                total_reports=total,
                false_reports=false_reports,
                last_report=datetime.utcnow() - timedelta(days=random.randint(1, 15)),
                reputation_score=1.0 - (false_reports / total if total > 0 else 0.5)
            )

            db.session.add(history)
            callers_created += 1

        # =========================
        # CROWD DETECTIONS
        # =========================
        crowd_locations = [
            (28.6139, 77.2090, "Connaught Place, Delhi",       "commercial"),
            (28.6448, 77.2167, "Chandni Chowk, Delhi",         "market"),
            (28.5535, 77.2588, "Nehru Stadium, Delhi",         "stadium"),
            (28.6129, 77.2295, "India Gate Lawns, Delhi",      "open_field"),
            (28.6562, 77.2410, "Yamuna Ghat Open Area, Delhi", "open_field"),
            (28.5245, 77.1855, "Saket District Park, Delhi",   "park"),
            (28.6356, 77.2245, "Kashmere Gate Bus Stand",      "transport_hub"),
            (28.5921, 77.0514, "Dwarka Sector 10 Ground",      "open_field"),
            (28.6431, 77.3152, "Akshardham Temple Grounds",    "religious_site"),
            (28.5706, 77.3210, "Noida Sector 18 Market",       "market"),
        ]

        crowds_created = 0
        for lat, lng, address, place_type in crowd_locations:
            # Add slight coordinate jitter for realism
            lat += random.uniform(-0.005, 0.005)
            lng += random.uniform(-0.005, 0.005)

            detection = detect_crowds_at_location(lat, lng, address, place_type)
            db.session.add(detection)
            crowds_created += 1

        # Commit
        db.session.commit()

        print("\n" + "=" * 50)
        print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print(f"📊 Created: {incidents_created} incidents")
        print(f"📊 Created: {resources_created} resources")
        print(f"📊 Created: {callers_created} caller histories")
        print(f"📊 Created: {crowds_created} crowd detections")

        print("\n🔍 Verification:")
        print(f"   - Incidents:         {Incident.query.count()}")
        print(f"   - Resources:         {Resource.query.count()}")
        print(f"   - Caller histories:  {CallerHistory.query.count()}")
        print(f"   - Crowd detections:  {CrowdDetection.query.count()}")

        # Print a quick crowd detection summary
        print("\n📍 Crowd Detection Summary:")
        for cd in CrowdDetection.query.all():
            anomaly_flag = " ⚠️  ANOMALOUS" if cd.is_anomalous else ""
            print(
                f"   [{cd.risk_level.upper():8s}] {cd.address:40s} | "
                f"~{cd.estimated_crowd_size:5d} people | "
                f"{cd.crowd_density:8s} | "
                f"via {cd.detection_source}{anomaly_flag}"
            )


if __name__ == "__main__":
    seed_database()
