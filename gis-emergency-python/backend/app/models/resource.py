# backend/app/models/resource.py
from datetime import datetime
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSON

# Import db from the same directory
from .database import db

class Resource(db.Model):
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    resource_type = db.Column(db.String(50), nullable=False)
    current_location = db.Column(Geometry('POINT', srid=4326), nullable=False)
    status = db.Column(db.String(20), default='available')
    capacity = db.Column(db.Integer)
    details = db.Column(JSON)
    last_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        coords = self.get_coordinates()
        return {
            'id': self.id,
            'type': self.resource_type,
            'status': self.status,
            'location': coords,
            'capacity': self.capacity,
            'details': self.details,
            'last_update': self.last_update.isoformat() if self.last_update else None
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
                'type': self.resource_type,
                'status': self.status,
                'capacity': self.capacity
            }
        }
    
    def get_coordinates(self):
        """Extract coordinates from PostGIS point"""
        if self.current_location:
            try:
                if hasattr(self.current_location, 'x') and hasattr(self.current_location, 'y'):
                    return {'lat': self.current_location.y, 'lng': self.current_location.x}
            except:
                pass
        return {'lat': 28.6139, 'lng': 77.2090}

class ResourceAllocation(db.Model):
    __tablename__ = 'resource_allocations'
    
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    estimated_arrival = db.Column(db.DateTime)
    actual_arrival = db.Column(db.DateTime)
    route = db.Column(Geometry('LINESTRING', srid=4326))
    distance_km = db.Column(db.Float)
    status = db.Column(db.String(20), default='dispatched')