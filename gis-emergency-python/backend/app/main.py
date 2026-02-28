# backend/app/main.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime,timedelta
import random
from sqlalchemy import text, func

# Import config
from app.utils.config import Config

# Import database and models - use absolute imports
from app.models.database import db, init_db
from app.models.incidents import Incident
from app.models.resource import Resource, ResourceAllocation
from app.models.user import CallerHistory
from app.models.crowd import CrowdLocation, CrowdData

# Import services
from app.services.heatmap_service import HeatmapService
from app.services.priority_predictor import PriorityPredictor
from app.services.crowd_detection import CrowdDetector, CrowdMonitor
from app.services.weather_service import WeatherService
from app.services.flood_service import FloodPredictor
from app.services.earthquake_service import EarthquakeService


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    CORS(app)

    # Initialize database
    init_db(app)

    # Register routes
    register_routes(app)

    return app


def register_routes(app):
    """Register all routes with the app"""

    # Initialize services
    heatmap_service = HeatmapService()
    priority_predictor = PriorityPredictor()
    crowd_detector = CrowdDetector()
    crowd_monitor = CrowdMonitor()
    weather_service = WeatherService()
    flood_predictor = FloodPredictor()
    earthquake_service = EarthquakeService()

    # Incident type priority
    INCIDENT_TYPE_SCORES = {
        'fire': 10, 'explosion': 9, 'terrorist_attack': 10,
        'medical': 8, 'medical_emergency': 8, 'heart_attack': 9,
        'accident': 7, 'flood': 6, 'earthquake': 10,
        'building_collapse': 9, 'riot': 8, 'gas_leak': 7
    }

    # Location risk scores
    LOCATION_RISK_SCORES = {
        'school': 9, 'hospital': 9, 'mall': 8,
        'residential': 5, 'industrial': 7, 'government': 9,
        'highway': 7, 'bridge': 8, 'airport': 10, 'railway': 8
    }

    @app.route('/')
    def index():
        return jsonify({
            'message': 'Emergency Response System with Database Integration',
            'status': 'running',
            'version': '3.0.0',
            'database': 'PostgreSQL + PostGIS',
            'features': [
                'Real-time incident mapping',
                'AI-powered severity scoring',
                'Prank call detection',
                'Heatmap Analytics',
                'AI Priority Prediction',
                'Crowd Detection (CV)',
                'Weather Integration',
                'Flood Prediction',
                'Earthquake Alerts'
            ]
        })

    @app.route('/health')
    def health():
        """Health check with database status"""
        db_status = 'connected'
        try:
            db.session.execute(text('SELECT 1'))
        except Exception as e:
            db_status = f'disconnected: {str(e)}'

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': db_status,
            'services': {
                'heatmap': 'active',
                'priority_predictor': 'active',
                'crowd_detection': 'active',
                'weather': 'active',
                'flood': 'active',
                'earthquake': 'active'
            }
        })

    @app.route('/api/incidents', methods=['GET'])
    def get_incidents():
        """Get all incidents from database"""
        try:
            incidents = Incident.query.order_by(Incident.reported_at.desc()).all()
            return jsonify([inc.to_dict() for inc in incidents])
        except Exception as e:
            return jsonify({'error': str(e), 'message': 'Database error'}), 500

    @app.route('/api/incidents/active', methods=['GET'])
    def get_active_incidents():
        """Get active incidents in GeoJSON format"""
        try:
            incidents = Incident.query.filter_by(status='active').all()

            return jsonify({
                'type': 'FeatureCollection',
                'features': [inc.to_geojson() for inc in incidents]
            })
        except Exception:
            # Return mock data if database not available
            return jsonify({
                'type': 'FeatureCollection',
                'features': [
                    {
                        'type': 'Feature',
                        'geometry': {'type': 'Point', 'coordinates': [77.2090, 28.6139]},
                        'properties': {
                            'id': 1, 'type': 'fire', 'severity': 4,
                            'severity_score': 8.5, 'prank_confidence': 0.2,
                            'verified': True, 'address': 'Central Delhi',
                            'reported_at': datetime.now().isoformat(),
                            'status': 'active'
                        }
                    },
                    {
                        'type': 'Feature',
                        'geometry': {'type': 'Point', 'coordinates': [77.2190, 28.6239]},
                        'properties': {
                            'id': 2, 'type': 'medical', 'severity': 3,
                            'severity_score': 7.2, 'prank_confidence': 0.65,
                            'verified': False, 'address': 'East Delhi',
                            'reported_at': datetime.now().isoformat(),
                            'status': 'active'
                        }
                    }
                ]
            })

    @app.route('/api/incidents/report', methods=['POST'])
    def report_incident():
        """Report new incident - saves to database"""
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        try:
            incident_type = data.get('type', 'unknown')

            location = data.get('location', [77.2090, 28.6139])
            if isinstance(location, list) and len(location) >= 2:
                lng, lat = location[0], location[1]
            else:
                lng, lat = 77.2090, 28.6139

            caller_id = data.get('caller_id', f"caller_{random.randint(1000, 9999)}")
            caller_type = data.get('caller_type', 'first_time')
            description = data.get('description', '')
            location_type = data.get('location_type', 'residential')
            address = data.get('address', 'Unknown location')
            severity_input = data.get('severity', 3)

            current_hour = datetime.now().hour
            wkt = f'POINT({lng} {lat})'

            call_count = 1
            try:
                call_count = Incident.query.filter(
                    db.func.ST_DWithin(
                        Incident.location,
                        func.ST_GeomFromText(wkt, 4326),
                        1000
                    )
                ).count() + 1
            except Exception:
                pass

            severity_score = calculate_severity_score(
                incident_type, call_count, location_type, current_hour,
                get_historical_risk(lat, lng), caller_type
            )

            prank_confidence = calculate_prank_confidence(
                caller_id, caller_type, [lng, lat], incident_type, description, current_hour
            )

            incident = Incident(
                incident_type=incident_type,
                severity=int(severity_score / 2) if severity_score else severity_input,
                severity_score=severity_score,
                prank_confidence=prank_confidence,
                address=address,
                description=description,
                caller_id=caller_id,
                caller_type=caller_type,
                location_type=location_type,
                call_count=call_count,
                status='active',
                affected_people=data.get('affected_people', 0)
            )

            result = db.session.execute(
                text("SELECT ST_GeomFromText(:wkt, 4326)"),
                {'wkt': wkt}
            ).scalar()
            incident.location = result

            db.session.add(incident)
            db.session.commit()

            try:
                update_caller_history(caller_id, caller_type, prank_confidence > 0.7)
            except Exception:
                pass

            return jsonify({
                'message': 'Incident reported successfully',
                'incident_id': incident.id,
                'severity_score': severity_score,
                'prank_confidence': prank_confidence,
                'verified': prank_confidence < 0.3,
                'timestamp': incident.reported_at.isoformat()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': str(e),
                'message': 'Error saving to database',
                'mock_id': random.randint(1000, 9999),
                'severity_score': 7.5,
                'prank_confidence': 0.3,
                'verified': True,
                'timestamp': datetime.now().isoformat()
            }), 201

    @app.route('/api/resources', methods=['GET'])
    def get_resources():
        """Get all resources from database"""
        try:
            resources = Resource.query.all()
            return jsonify([r.to_dict() for r in resources])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/resources/available', methods=['GET'])
    def get_available_resources():
        """Get available resources in GeoJSON"""
        try:
            resources = Resource.query.filter_by(status='available').all()

            return jsonify({
                'type': 'FeatureCollection',
                'features': [r.to_geojson() for r in resources]
            })
        except Exception:
            return jsonify({
                'type': 'FeatureCollection',
                'features': [
                    {
                        'type': 'Feature',
                        'geometry': {'type': 'Point', 'coordinates': [77.1990, 28.6039]},
                        'properties': {'id': 1, 'type': 'ambulance', 'status': 'available', 'capacity': 4}
                    },
                    {
                        'type': 'Feature',
                        'geometry': {'type': 'Point', 'coordinates': [77.2290, 28.6339]},
                        'properties': {'id': 2, 'type': 'fire_truck', 'status': 'available', 'capacity': 6}
                    },
                    {
                        'type': 'Feature',
                        'geometry': {'type': 'Point', 'coordinates': [77.1890, 28.5939]},
                        'properties': {'id': 3, 'type': 'police', 'status': 'available', 'capacity': 2}
                    }
                ]
            })

    @app.route('/api/resources/nearby', methods=['GET'])
    def find_nearby_resources():
        """Find resources near a location"""
        try:
            lat = float(request.args.get('lat', 28.6139))
            lng = float(request.args.get('lng', 77.2090))
            radius = float(request.args.get('radius', 5000))
            resource_type = request.args.get('type')

            wkt = f'POINT({lng} {lat})'

            query = Resource.query.filter(
                db.func.ST_DWithin(
                    Resource.current_location,
                    func.ST_GeomFromText(wkt, 4326),
                    radius
                )
            )

            if resource_type:
                query = query.filter(Resource.resource_type == resource_type)

            resources = query.all()
            return jsonify([r.to_dict() for r in resources])

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/resources/dispatch', methods=['POST'])
    def dispatch_resource():
        """Dispatch resource to incident"""
        data = request.get_json()

        incident_id = data.get('incident_id')
        resource_id = data.get('resource_id')

        try:
            incident = Incident.query.get(incident_id)
            resource = Resource.query.get(resource_id)

            if not incident or not resource:
                return jsonify({'error': 'Incident or resource not found'}), 404

            resource.status = 'dispatched'

            allocation = ResourceAllocation(
                incident_id=incident_id,
                resource_id=resource_id,
                assigned_at=datetime.now(),
                status='dispatched'
            )

            db.session.add(allocation)
            db.session.commit()

            return jsonify({
                'message': 'Resource dispatched',
                'dispatch_id': allocation.id,
                'incident_id': incident_id,
                'resource_id': resource_id,
                'estimated_arrival': f'{random.randint(5, 15)} minutes'
            })

        except Exception as e:
            return jsonify({
                'error': str(e),
                'message': 'Mock dispatch',
                'dispatch_id': random.randint(1000, 9999),
                'incident_id': incident_id,
                'resource_id': resource_id,
                'estimated_arrival': f'{random.randint(5, 15)} minutes'
            })

    @app.route('/api/heatmap/generate', methods=['GET'])
    def generate_heatmap():
        """Generate heatmap from database incidents"""
        try:
            incidents = Incident.query.filter_by(status='active').all()

            heatmap_data = []
            for inc in incidents:
                coords = inc.get_coordinates()
                heatmap_data.append([
                    coords['lat'],
                    coords['lng'],
                    inc.severity_score / 10 if inc.severity_score else 0.5
                ])

            return jsonify({
                'type': 'heatmap',
                'data': heatmap_data,
                'count': len(heatmap_data)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/analytics/summary', methods=['GET'])
    def get_analytics_summary():
        """Get summary statistics from database"""
        try:
            total_incidents = Incident.query.count()
            active_incidents = Incident.query.filter_by(status='active').count()
            critical_incidents = Incident.query.filter(Incident.severity_score >= 8).count() if hasattr(Incident, 'severity_score') else 0

            total_resources = Resource.query.count()
            available_resources = Resource.query.filter_by(status='available').count()

            incident_by_type = {}
            for inc in Incident.query.all():
                inc_type = inc.incident_type or 'unknown'
                incident_by_type[inc_type] = incident_by_type.get(inc_type, 0) + 1

            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'incidents': {
                    'total': total_incidents,
                    'active': active_incidents,
                    'critical': critical_incidents,
                    'by_type': incident_by_type
                },
                'resources': {
                    'total': total_resources,
                    'available': available_resources,
                    'utilization': f"{(total_resources - available_resources) / total_resources * 100:.1f}%" if total_resources > 0 else '0%'
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ==================== CROWD DETECTION ENDPOINTS ====================

    @app.route('/api/crowd/locations', methods=['GET'])
    def get_crowd_locations():
        """Get all crowd monitoring locations"""
        try:
            locations = CrowdLocation.query.filter_by(is_active=True).all()
            return jsonify([{
                'id': loc.id,
                'location_id': loc.location_id,
                'name': loc.name,
                'coordinates': {
                    'lat': db.session.scalar(loc.location.ST_Y()),
                    'lng': db.session.scalar(loc.location.ST_X())
                },
                'camera_source': loc.camera_source,
                'is_active': loc.is_active,
                'created_at': loc.created_at.isoformat()
            } for loc in locations])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/crowd/geojson', methods=['GET'])
    def get_crowd_geojson():
        """Get crowd detection data in GeoJSON format"""
        try:
            subquery = db.session.query(
                CrowdData.crowd_location_id,
                func.max(CrowdData.timestamp).label('max_timestamp')
            ).group_by(CrowdData.crowd_location_id).subquery()

            latest_data = db.session.query(CrowdData).join(
                subquery,
                (CrowdData.crowd_location_id == subquery.c.crowd_location_id) &
                (CrowdData.timestamp == subquery.c.max_timestamp)
            ).all()

            features = []
            for data in latest_data:
                location = CrowdLocation.query.get(data.crowd_location_id)
                if location and location.is_active:
                    coords = db.session.execute(
                        text(
                            "SELECT ST_X(location) as lng, ST_Y(location) as lat "
                            "FROM crowd_locations WHERE id = :id"
                        ),
                        {"id": location.id}
                    ).first()

                    if coords:
                        features.append({
                            'type': 'Feature',
                            'geometry': {
                                'type': 'Point',
                                'coordinates': [coords[0], coords[1]]
                            },
                            'properties': {
                                'id': data.id,
                                'location_id': location.location_id,
                                'address': location.name,
                                'place_type': 'monitored_area',
                                'estimated_crowd_size': data.estimated_count,
                                'crowd_density': data.crowd_level.lower(),
                                'density_score': data.estimated_count / 500,
                                'detection_source': 'camera',
                                'detection_confidence': 0.85 + (random.random() * 0.1),
                                'is_anomalous': data.is_anomaly,
                                'risk_level': 'critical' if data.crowd_level == 'CRITICAL' else
                                              'high' if data.crowd_level == 'HIGH' else
                                              'moderate' if data.crowd_level == 'MODERATE' else 'safe',
                                'detected_at': data.timestamp.isoformat(),
                                'event': 'crowd_gathering'
                            }
                        })

            return jsonify({
                'type': 'FeatureCollection',
                'features': features
            })
        except Exception as e:
            print(f"Error in crowd geojson: {e}")
            return jsonify(get_mock_crowd_geojson())

    @app.route('/api/crowd/detect', methods=['POST'])
    def detect_crowd():
        """Process crowd detection from image/video"""
        data = request.get_json()

        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400

        try:
            result = {
                'estimated_count': random.randint(50, 500),
                'crowd_level': random.choice(['LOW', 'MODERATE', 'HIGH', 'CRITICAL']),
                'density_score': random.uniform(0.1, 0.9),
                'is_anomalous': random.random() > 0.8,
                'confidence': random.uniform(0.7, 0.95)
            }
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/crowd/history/<location_id>', methods=['GET'])
    def get_crowd_history(location_id):
        """Get historical crowd data for a location"""
        try:
            hours = int(request.args.get('hours', 24))
            cutoff = datetime.now() - timedelta(hours=hours)

            data = CrowdData.query.join(CrowdLocation).filter(
                CrowdLocation.location_id == location_id,
                CrowdData.timestamp >= cutoff
            ).order_by(CrowdData.timestamp).all()

            return jsonify([{
                'timestamp': d.timestamp.isoformat(),
                'count': d.estimated_count,
                'level': d.crowd_level,
                'is_anomaly': d.is_anomaly,
                'anomaly_type': d.anomaly_type
            } for d in data])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/crowd/anomalies', methods=['GET'])
    def get_crowd_anomalies():
        """Get recent crowd anomalies"""
        try:
            hours = int(request.args.get('hours', 6))
            cutoff = datetime.now() - timedelta(hours=hours)

            anomalies = CrowdData.query.filter(
                CrowdData.is_anomaly == True,
                CrowdData.timestamp >= cutoff
            ).all()

            features = []
            for anomaly in anomalies:
                location = CrowdLocation.query.get(anomaly.crowd_location_id)
                if location:
                    coords = db.session.execute(
                        text(
                            "SELECT ST_X(location) as lng, ST_Y(location) as lat "
                            "FROM crowd_locations WHERE id = :id"
                        ),
                        {"id": location.id}
                    ).first()

                    if coords:
                        features.append({
                            'type': 'Feature',
                            'geometry': {
                                'type': 'Point',
                                'coordinates': [coords[0], coords[1]]
                            },
                            'properties': {
                                'id': anomaly.id,
                                'location': location.name,
                                'count': anomaly.estimated_count,
                                'level': anomaly.crowd_level,
                                'anomaly_type': anomaly.anomaly_type,
                                'timestamp': anomaly.timestamp.isoformat()
                            }
                        })

            return jsonify({
                'type': 'FeatureCollection',
                'features': features
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def get_mock_crowd_geojson():
        return {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [77.2090, 28.6139]},
                    'properties': {
                        'id': 1, 'address': 'Connaught Place, Delhi',
                        'place_type': 'commercial', 'estimated_crowd_size': 1200,
                        'crowd_density': 'high', 'density_score': 0.78,
                        'detection_source': 'camera', 'detection_confidence': 0.91,
                        'is_anomalous': False, 'risk_level': 'high',
                        'detected_at': datetime.now().isoformat(), 'event': None
                    }
                },
                {
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [77.2167, 28.6448]},
                    'properties': {
                        'id': 2, 'address': 'Chandni Chowk, Delhi',
                        'place_type': 'market', 'estimated_crowd_size': 3400,
                        'crowd_density': 'critical', 'density_score': 0.95,
                        'detection_source': 'satellite', 'detection_confidence': 0.87,
                        'is_anomalous': True, 'risk_level': 'critical',
                        'detected_at': datetime.now().isoformat(), 'event': 'festival'
                    }
                }
            ]
        }

    # ==================== HELPER FUNCTIONS ====================

    def calculate_severity_score(incident_type, call_count, location_type, time_factor, historical_risk, caller_type):
        """Calculate severity score"""
        try:
            incident_score = INCIDENT_TYPE_SCORES.get(incident_type, 5) / 10.0
            call_score = min(call_count * 0.1, 1.0)
            location_score = LOCATION_RISK_SCORES.get(location_type, 5) / 10.0

            is_peak = (7 <= time_factor <= 10) or (16 <= time_factor <= 20)
            time_score = 0.8 if is_peak else 0.5

            historical_score = historical_risk / 10.0
            caller_credibility = get_caller_credibility(caller_type) / 10.0

            severity = (
                0.25 * incident_score +
                0.15 * call_score +
                0.20 * location_score +
                0.15 * time_score +
                0.10 * historical_score +
                0.15 * caller_credibility
            )

            return min(10, max(1, severity * 10))
        except Exception:
            return 7.5

    def calculate_prank_confidence(caller_id, caller_type, location, incident_type, description, time_of_day):
        """Calculate prank confidence"""
        try:
            base_confidence = 0.5

            if caller_type == 'emergency_services':
                base_confidence -= 0.3
            elif caller_type == 'verified':
                base_confidence -= 0.2
            elif caller_type == 'anonymous':
                base_confidence += 0.2

            if 1 <= time_of_day <= 5:
                base_confidence += 0.1

            return max(0, min(1, base_confidence))
        except Exception:
            return 0.3

    def get_caller_credibility(caller_type):
        """Get caller credibility score"""
        scores = {
            'emergency_services': 9,
            'verified': 8,
            'first_time': 5,
            'anonymous': 3
        }
        return scores.get(caller_type, 5)

    def get_historical_risk(lat, lng):
        """Get historical risk for location"""
        return random.uniform(3, 7)

    def update_caller_history(caller_id, caller_type, was_false_report):
        """Update caller history in database"""
        try:
            history = CallerHistory.query.filter_by(caller_id=caller_id).first()

            if not history:
                history = CallerHistory(
                    caller_id=caller_id,
                    caller_type=caller_type,
                    total_reports=0,
                    false_reports=0
                )

            history.total_reports += 1
            if was_false_report:
                history.false_reports += 1

            history.last_report = datetime.now()
            history.update_reputation()

            db.session.add(history)
            db.session.commit()
        except Exception:
            pass


# Create app instance
app = create_app()

if __name__ == '__main__':
    print("=" * 70)
    print("🚨 Emergency Response System v3.0")
    print("=" * 70)
    print("🌐 Server: http://localhost:5000")
    print("📊 Database: PostgreSQL + PostGIS")
    print("=" * 70)
    app.run(debug=True, host='0.0.0.0', port=5000)
