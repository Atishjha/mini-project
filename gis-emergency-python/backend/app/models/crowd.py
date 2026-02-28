# backend/app/models/crowd.py
from .database import db
from geoalchemy2 import Geometry
from datetime import datetime

class CrowdLocation(db.Model):
    __tablename__ = 'crowd_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(200))
    location = db.Column(Geometry('POINT', srid=4326))
    camera_source = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    readings = db.relationship('CrowdData', backref='location', lazy=True)

class CrowdData(db.Model):
    __tablename__ = 'crowd_data'
    
    id = db.Column(db.Integer, primary_key=True)
    crowd_location_id = db.Column(db.Integer, db.ForeignKey('crowd_locations.id'))
    estimated_count = db.Column(db.Integer)
    crowd_level = db.Column(db.String(20))
    density_map = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_anomaly = db.Column(db.Boolean, default=False)
    anomaly_type = db.Column(db.String(50))
