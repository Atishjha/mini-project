# backend/app/models/incidents.py

from datetime import datetime
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSON

from .database import db


class Incident(db.Model):
    __tablename__ = 'incidents'

    # =========================
    # Basic Incident Info
    # =========================
    id = db.Column(db.Integer, primary_key=True)

    # Type of emergency (fire, accident, flood, etc.)
    incident_type = db.Column(db.String(50), nullable=False)

    # Severity level (1–10 or scaled value)
    severity = db.Column(db.Integer, nullable=False)

    # Geographic location stored as PostGIS POINT (longitude/latitude)
    location = db.Column(Geometry('POINT', srid=4326), nullable=False)

    address = db.Column(db.String(200))

    # Time incident was reported
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Status: active, resolved, pending
    status = db.Column(db.String(20), default='active')

    description = db.Column(db.Text)

    affected_people = db.Column(db.Integer)

    # =========================
    # 🔥 Prank Detection Fields
    # =========================

    # Confidence score (0.0 – 1.0) predicting if it's a prank call
    prank_confidence = db.Column(db.Float, default=0.0)

    # Whether the incident has been verified by authorities
    verified = db.Column(db.Boolean, default=False)

    # Caller identification
    caller_id = db.Column(db.String(50))

    # Caller type (citizen, anonymous, agency, etc.)
    caller_type = db.Column(db.String(50))

    # Location type classification
    location_type = db.Column(db.String(50))

    # Number of times this incident was reported
    call_count = db.Column(db.Integer, default=1)

    # =========================
    # Relationships
    # =========================
    resources = db.relationship('ResourceAllocation', backref='incident', lazy=True)

    # =========================
    # Utility Methods
    # =========================

    def to_dict(self):
        """Convert incident to dictionary format"""
        coords = self.get_coordinates()
        return {
            'id': self.id,
            'type': self.incident_type,
            'severity': self.severity,
            'location': coords,
            'address': self.address,
            'reported_at': self.reported_at.isoformat() if self.reported_at else None,
            'status': self.status,
            'description': self.description,
            'affected_people': self.affected_people,
            'prank_confidence': self.prank_confidence,
            'verified': self.verified,
            'caller_id': self.caller_id,
            'caller_type': self.caller_type,
            'location_type': self.location_type,
            'call_count': self.call_count
        }

    def to_geojson(self):
        """Convert to GeoJSON feature format"""
        coords = self.get_coordinates()
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [coords['lng'], coords['lat']]
            },
            'properties': {
                'id': self.id,
                'type': self.incident_type,
                'severity': self.severity,
                'address': self.address,
                'reported_at': self.reported_at.isoformat() if self.reported_at else None,
                'status': self.status,
                'prank_confidence': self.prank_confidence,
                'verified': self.verified
            }
        }

    def get_coordinates(self):
        """Extract coordinates from PostGIS POINT"""
        if self.location:
            try:
                if hasattr(self.location, 'x') and hasattr(self.location, 'y'):
                    return {'lat': self.location.y, 'lng': self.location.x}
            except Exception:
                pass

        # Default fallback (Delhi coordinates)
        return {'lat': 28.6139, 'lng': 77.2090}