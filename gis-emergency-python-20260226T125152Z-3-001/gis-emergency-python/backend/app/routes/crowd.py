from flask import Blueprint, jsonify, request

bp = Blueprint('crowd', __name__)

# ─────────────────────────────────────────────
# In-memory mock data (mirrors seed.py output)
# Replace with DB queries once CrowdDetection
# model is imported, e.g.:
#   from ..models.crowd import CrowdDetection
#   detections = CrowdDetection.query.all()
#   return jsonify([d.to_dict() for d in detections])
# ─────────────────────────────────────────────

MOCK_CROWDS = [
    {
        'id': 1,
        'address': 'Connaught Place, Delhi',
        'place_type': 'commercial',
        'estimated_crowd_size': 1200,
        'crowd_density': 'high',
        'density_score': 0.78,
        'detection_source': 'camera',
        'detection_confidence': 0.91,
        'is_anomalous': False,
        'risk_level': 'high',
        'detected_at': '2024-01-15T10:00:00',
        'location': {'lat': 28.6139, 'lng': 77.2090},
        'extra_metadata': {'weather': 'clear', 'event': None}
    },
    {
        'id': 2,
        'address': 'Chandni Chowk, Delhi',
        'place_type': 'market',
        'estimated_crowd_size': 3400,
        'crowd_density': 'critical',
        'density_score': 0.95,
        'detection_source': 'satellite',
        'detection_confidence': 0.87,
        'is_anomalous': True,
        'risk_level': 'critical',
        'detected_at': '2024-01-15T09:30:00',
        'location': {'lat': 28.6448, 'lng': 77.2167},
        'extra_metadata': {'weather': 'sunny', 'event': 'festival'}
    },
    {
        'id': 3,
        'address': 'India Gate Lawns, Delhi',
        'place_type': 'open_field',
        'estimated_crowd_size': 450,
        'crowd_density': 'moderate',
        'density_score': 0.42,
        'detection_source': 'drone',
        'detection_confidence': 0.95,
        'is_anomalous': False,
        'risk_level': 'moderate',
        'detected_at': '2024-01-15T11:00:00',
        'location': {'lat': 28.6129, 'lng': 77.2295},
        'extra_metadata': {'weather': 'cloudy', 'event': None}
    },
    {
        'id': 4,
        'address': 'Nehru Stadium, Delhi',
        'place_type': 'stadium',
        'estimated_crowd_size': 28000,
        'crowd_density': 'critical',
        'density_score': 0.98,
        'detection_source': 'sensor',
        'detection_confidence': 0.99,
        'is_anomalous': False,
        'risk_level': 'critical',
        'detected_at': '2024-01-15T08:45:00',
        'location': {'lat': 28.5535, 'lng': 77.2588},
        'extra_metadata': {'weather': 'clear', 'event': 'sports_event'}
    },
    {
        'id': 5,
        'address': 'Yamuna Ghat Open Area, Delhi',
        'place_type': 'open_field',
        'estimated_crowd_size': 80,
        'crowd_density': 'low',
        'density_score': 0.12,
        'detection_source': 'drone',
        'detection_confidence': 0.82,
        'is_anomalous': False,
        'risk_level': 'safe',
        'detected_at': '2024-01-15T07:00:00',
        'location': {'lat': 28.6562, 'lng': 77.2410},
        'extra_metadata': {'weather': 'clear', 'event': None}
    },
    {
        'id': 6,
        'address': 'Kashmere Gate Bus Stand',
        'place_type': 'transport_hub',
        'estimated_crowd_size': 2100,
        'crowd_density': 'high',
        'density_score': 0.81,
        'detection_source': 'camera',
        'detection_confidence': 0.93,
        'is_anomalous': True,
        'risk_level': 'high',
        'detected_at': '2024-01-15T06:30:00',
        'location': {'lat': 28.6356, 'lng': 77.2245},
        'extra_metadata': {'weather': 'cloudy', 'event': None}
    },
    {
        'id': 7,
        'address': 'Akshardham Temple Grounds',
        'place_type': 'religious_site',
        'estimated_crowd_size': 5000,
        'crowd_density': 'critical',
        'density_score': 0.92,
        'detection_source': 'satellite',
        'detection_confidence': 0.88,
        'is_anomalous': False,
        'risk_level': 'critical',
        'detected_at': '2024-01-15T10:15:00',
        'location': {'lat': 28.6431, 'lng': 77.3152},
        'extra_metadata': {'weather': 'sunny', 'event': None}
    },
    {
        'id': 8,
        'address': 'Saket District Park, Delhi',
        'place_type': 'park',
        'estimated_crowd_size': 200,
        'crowd_density': 'low',
        'density_score': 0.18,
        'detection_source': 'camera',
        'detection_confidence': 0.76,
        'is_anomalous': False,
        'risk_level': 'safe',
        'detected_at': '2024-01-15T08:00:00',
        'location': {'lat': 28.5245, 'lng': 77.1855},
        'extra_metadata': {'weather': 'clear', 'event': None}
    },
    {
        'id': 9,
        'address': 'Dwarka Sector 10 Ground',
        'place_type': 'open_field',
        'estimated_crowd_size': 310,
        'crowd_density': 'moderate',
        'density_score': 0.38,
        'detection_source': 'drone',
        'detection_confidence': 0.84,
        'is_anomalous': False,
        'risk_level': 'moderate',
        'detected_at': '2024-01-15T09:00:00',
        'location': {'lat': 28.5921, 'lng': 77.0514},
        'extra_metadata': {'weather': 'rainy', 'event': None}
    },
    {
        'id': 10,
        'address': 'Noida Sector 18 Market',
        'place_type': 'market',
        'estimated_crowd_size': 1800,
        'crowd_density': 'high',
        'density_score': 0.74,
        'detection_source': 'camera',
        'detection_confidence': 0.90,
        'is_anomalous': False,
        'risk_level': 'high',
        'detected_at': '2024-01-15T11:30:00',
        'location': {'lat': 28.5706, 'lng': 77.3210},
        'extra_metadata': {'weather': 'sunny', 'event': None}
    },
]


@bp.route('/', methods=['GET'])
def get_crowd_detections():
    """Get all crowd detections"""
    risk_filter = request.args.get('risk_level')       # ?risk_level=critical
    place_filter = request.args.get('place_type')      # ?place_type=open_field
    anomalous_only = request.args.get('anomalous')     # ?anomalous=true

    results = MOCK_CROWDS

    if risk_filter:
        results = [c for c in results if c['risk_level'] == risk_filter]
    if place_filter:
        results = [c for c in results if c['place_type'] == place_filter]
    if anomalous_only and anomalous_only.lower() == 'true':
        results = [c for c in results if c['is_anomalous']]

    return jsonify(results)


@bp.route('/geojson', methods=['GET'])
def get_crowd_geojson():
    """Get crowd detections in GeoJSON format (for map display)"""
    features = []
    for c in MOCK_CROWDS:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [c['location']['lng'], c['location']['lat']]
            },
            'properties': {
                'id': c['id'],
                'address': c['address'],
                'place_type': c['place_type'],
                'estimated_crowd_size': c['estimated_crowd_size'],
                'crowd_density': c['crowd_density'],
                'density_score': c['density_score'],
                'detection_source': c['detection_source'],
                'detection_confidence': c['detection_confidence'],
                'is_anomalous': c['is_anomalous'],
                'risk_level': c['risk_level'],
                'detected_at': c['detected_at'],
                'event': c['extra_metadata'].get('event'),
                'weather': c['extra_metadata'].get('weather'),
            }
        })

    return jsonify({
        'type': 'FeatureCollection',
        'features': features
    })


@bp.route('/<int:crowd_id>', methods=['GET'])
def get_crowd_detection(crowd_id):
    """Get a specific crowd detection by ID"""
    result = next((c for c in MOCK_CROWDS if c['id'] == crowd_id), None)
    if result is None:
        return jsonify({'error': 'Crowd detection not found'}), 404
    return jsonify(result)


@bp.route('/summary', methods=['GET'])
def get_crowd_summary():
    """Get a summary count by risk level"""
    summary = {'safe': 0, 'moderate': 0, 'high': 0, 'critical': 0}
    for c in MOCK_CROWDS:
        summary[c['risk_level']] += 1
    return jsonify({
        'total': len(MOCK_CROWDS),
        'anomalous': sum(1 for c in MOCK_CROWDS if c['is_anomalous']),
        'by_risk_level': summary
    })
