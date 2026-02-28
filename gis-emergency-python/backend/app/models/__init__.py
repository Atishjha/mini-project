# backend/app/models/__init__.py
from .database import db, init_db
from .incidents import Incident
from .resource import Resource, ResourceAllocation
from .user import User, CallerHistory
from .zone import RiskZone, FloodZone
from .crowd import CrowdLocation, CrowdData



__all__ = [
    'db', 'init_db',
    'Incident',
    'Resource', 'ResourceAllocation',
    'User', 'CallerHistory',
    'RiskZone', 'FloodZone',
    'CrowdLocation', 'CrowdData'
]
