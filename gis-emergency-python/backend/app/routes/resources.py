from flask import Blueprint, jsonify,request

bp = Blueprint('resources', __name__)

@bp.route('/', methods=['GET'])
def get_resources():
    """Get all resources"""
    resources = [
        {
            'id': 1,
            'type': 'ambulance',
            'location': {'lat': 28.6039, 'lng': 77.1990},
            'status': 'available',
            'capacity': 4
        },
        {
            'id': 2,
            'type': 'fire_truck',
            'location': {'lat': 28.6339, 'lng': 77.2290},
            'status': 'available',
            'capacity': 6
        },
        {
            'id': 3,
            'type': 'police',
            'location': {'lat': 28.5939, 'lng': 77.1890},
            'status': 'available',
            'capacity': 2
        }
    ]
    return jsonify(resources)

@bp.route('/available', methods=['GET'])
def get_available_resources():
    """Get available resources in GeoJSON format"""
    geojson = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [77.1990, 28.6039]
                },
                'properties': {
                    'id': 1,
                    'type': 'ambulance',
                    'status': 'available',
                    'capacity': 4
                }
            },
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [77.2290, 28.6339]
                },
                'properties': {
                    'id': 2,
                    'type': 'fire_truck',
                    'status': 'available',
                    'capacity': 6
                }
            },
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [77.1890, 28.5939]
                },
                'properties': {
                    'id': 3,
                    'type': 'police',
                    'status': 'available',
                    'capacity': 2
                }
            }
        ]
    }
    return jsonify(geojson)

@bp.route('/nearest', methods=['GET'])
def get_nearest_resources():
    """Find nearest resources to a location"""
    lat = float(request.args.get('lat', 28.6139))
    lng = float(request.args.get('lng', 77.2090))
    resource_type = request.args.get('type')
    
    # Mock response
    return jsonify({
        'nearest_to': {'lat': lat, 'lng': lng},
        'resources': [
            {
                'id': 1,
                'type': 'ambulance',
                'distance_km': 5.2,
                'eta_minutes': 8
            },
            {
                'id': 2,
                'type': 'fire_truck',
                'distance_km': 7.8,
                'eta_minutes': 12
            }
        ]
    })