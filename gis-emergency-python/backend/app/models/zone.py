# backend/app/models/zone.py
from .database import db
from geoalchemy2 import Geometry
from datetime import datetime

class RiskZone(db.Model):
    __tablename__ = 'risk_zones'
    
    id = db.Column(db.Integer, primary_key=True)
    zone_type = db.Column(db.String(50))
    risk_level = db.Column(db.String(20))
    geometry = db.Column(Geometry('POLYGON', srid=4326))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    def to_geojson(self):
        """Convert to GeoJSON"""
        return {
            'type': 'Feature',
            'geometry': db.session.scalar(self.geometry.ST_AsGeoJSON()),
            'properties': {
                'id': self.id,
                'zone_type': self.zone_type,
                'risk_level': self.risk_level,
                'description': self.description,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None
            }
        }

class FloodZone(db.Model):
    __tablename__ = 'flood_zones'
    
    id = db.Column(db.Integer, primary_key=True)
    risk_score = db.Column(db.Float)
    risk_level = db.Column(db.String(20))
    water_level = db.Column(db.Float)
    geometry = db.Column(Geometry('POLYGON', srid=4326))
    predicted_at = db.Column(db.DateTime, default=datetime.utcnow)
    population_affected = db.Column(db.Integer)