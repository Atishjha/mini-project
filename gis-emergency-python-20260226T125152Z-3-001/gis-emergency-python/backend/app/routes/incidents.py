from flask import Blueprint, jsonify, request
from ..main import db
import json

bp = Blueprint('incidents', __name__)

@bp.route('/', methods=['GET'])
def get_incidents():
    """Get all active incidents"""
    # Temporary mock data
    incidents = [
        {
            'id': 1,
            'type': 'fire',
            'severity': 4,
            'location': {'lat': 28.6139, 'lng': 77.2090},
            'address': 'Central Delhi',
            'status': 'active',
            'reported_at': '2024-01-15T10:30:00'
        },
        {
            'id': 2,
            'type': 'medical',
            'severity': 3,
            'location': {'lat': 28.6239, 'lng': 77.2190},
            'address': 'East Delhi',
            'status': 'active',
            'reported_at': '2024-01-15T11:15:00'
        }
    ]
    return jsonify(incidents)

@bp.route('/', methods=['POST'])
def create_incident():
    """Create a new incident"""
    data = request.get_json()
    return jsonify({
        'message': 'Incident created successfully',
        'id': 3,
        **data
    }), 201

@bp.route('/<int:incident_id>', methods=['GET'])
def get_incident(incident_id):
    """Get a specific incident"""
    return jsonify({
        'id': incident_id,
        'type': 'fire',
        'severity': 4,
        'location': {'lat': 28.6139, 'lng': 77.2090},
        'status': 'active'
    })

@bp.route('/active', methods=['GET'])
def get_active_incidents():
    """Get active incidents in GeoJSON format"""
    geojson = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [77.2090, 28.6139]
                },
                'properties': {
                    'id': 1,
                    'incident_type': 'fire',
                    'severity': 4,
                    'reported_at': '2024-01-15T10:30:00',
                    'status': 'active',
                    'address': 'Central Delhi'
                }
            },
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [77.2190, 28.6239]
                },
                'properties': {
                    'id': 2,
                    'incident_type': 'medical',
                    'severity': 3,
                    'reported_at': '2024-01-15T11:15:00',
                    'status': 'active',
                    'address': 'East Delhi'
                }
            }
        ]
    }
    return jsonify(geojson)