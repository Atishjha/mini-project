# backend/app/models/incidents.py
from datetime import datetime
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSON

# Import db from the same directory
from .database import db

class Incident(db.Model):
    __tablename__ = 'incidents'
    
    id = db.Column(db.Integer, primary_key=True)
    incident_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.Integer, nullable=False)
    location = db.Column(Geometry('POINT', srid=4326), nullable=False)
    address = db.Column(db.String(200))
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    description = db.Column(db.Text)
    affected_people = db.Column(db.Integer)
    
    # Relationships
    resources = db.relationship('ResourceAllocation', backref='incident', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary"""
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
            'affected_people': self.affected_people
        }
    
    def to_geojson(self):
        """Convert to GeoJSON feature"""
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
                'status': self.status
            }
        }
    
    def get_coordinates(self):
        """Extract coordinates from PostGIS point"""
        if self.location:
            try:
                if hasattr(self.location, 'x') and hasattr(self.location, 'y'):
                    return {'lat': self.location.y, 'lng': self.location.x}
            except:
                pass
        return {'lat': 28.6139, 'lng': 77.2090}