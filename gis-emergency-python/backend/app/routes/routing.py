from flask import Blueprint, jsonify, request
import random

bp = Blueprint('routing', __name__)

@bp.route('/optimize', methods=['POST'])
def optimize_route():
    """Calculate optimal route"""
    data = request.get_json()
    
    # Mock response
    return jsonify({
        'route': {
            'distance_km': random.uniform(3, 10),
            'duration_min': random.uniform(5, 20),
            'geometry': {
                'type': 'LineString',
                'coordinates': [
                    [data['start']['lng'], data['start']['lat']],
                    [data['end']['lng'], data['end']['lat']]
                ]
            }
        },
        'waypoints': [
            {'lat': data['start']['lat'], 'lng': data['start']['lng']},
            {'lat': data['end']['lat'], 'lng': data['end']['lng']}
        ]
    })

@bp.route('/dispatch', methods=['POST'])
def dispatch_resource():
    """Dispatch resource to incident"""
    data = request.get_json()
    
    return jsonify({
        'message': 'Resource dispatched successfully',
        'dispatch_id': random.randint(1000, 9999),
        'estimated_arrival': '10-15 minutes',
        'incident_id': data.get('incident_id'),
        'resource_id': data.get('resource_id')
    })