from flask import Flask, jsonify, request
from flask_cors import CORS
import random
from datetime import datetime
import math

app = Flask(__name__)
CORS(app)

# Weights for severity calculation
SEVERITY_WEIGHTS = {
    'incident_type': 0.3,
    'call_frequency': 0.2,
    'location_risk': 0.25,
    'time_factor': 0.15,
    'historical_data': 0.1
}

# Incident type priority (higher = more severe)
INCIDENT_TYPE_SCORES = {
    'fire': 10,
    'explosion': 9,
    'terrorist_attack': 10,
    'medical': 8,
    'medical_emergency': 8,
    'heart_attack': 9,
    'accident': 7,
    'flood': 6,
    'earthquake': 10,
    'building_collapse': 9,
    'riot': 8,
    'gas_leak': 7
}

# Location risk scores
LOCATION_RISK_SCORES = {
    'school': 9,
    'hospital': 9,
    'mall': 8,
    'residential': 5,
    'industrial': 7,
    'government': 9,
    'highway': 7,
    'bridge': 8,
    'airport': 10,
    'railway': 8,
    'airport': 10
}

# Mock caller database (in production, would be real database)
caller_history = {}

@app.route('/')
def index():
    return jsonify({
        'message': 'Emergency Response System API with AI Severity Scoring',
        'status': 'running',
        'version': '2.0.0',
        'features': [
            'Real-time incident mapping',
            'AI-powered severity scoring',
            'Prank call detection',
            'Resource optimization',
            'Multi-factor verification'
        ],
        'endpoints': {
            'GET /': 'API information',
            'GET /health': 'Health check',
            'GET /api/incidents': 'All incidents',
            'GET /api/incidents/active': 'Active incidents (GeoJSON)',
            'GET /api/resources': 'All resources',
            'GET /api/resources/available': 'Available resources (GeoJSON)',
            'POST /api/incidents/report': 'Report new incident',
            'POST /api/routing/dispatch': 'Dispatch resource'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/incidents')
def get_incidents():
    """Get all incidents"""
    return jsonify([
        {
            'id': 1, 
            'type': 'fire', 
            'severity': 4, 
            'location': [77.2090, 28.6139],
            'address': 'Central Delhi, Connaught Place',
            'reported_at': '2024-01-15T10:30:00',
            'status': 'active',
            'description': 'Building fire, 3rd floor'
        },
        {
            'id': 2, 
            'type': 'medical', 
            'severity': 3, 
            'location': [77.2190, 28.6239],
            'address': 'East Delhi, Preet Vihar',
            'reported_at': '2024-01-15T11:15:00',
            'status': 'active',
            'description': 'Heart attack patient needs urgent care'
        },
        {
            'id': 3,
            'type': 'accident',
            'severity': 5,
            'location': [77.2290, 28.6099],
            'address': 'South Delhi, Saket',
            'reported_at': '2024-01-15T12:00:00',
            'status': 'active',
            'description': 'Multiple vehicle collision on main road'
        }
    ])

@app.route('/api/incidents/active')
def get_active_incidents():
    """Get active incidents in GeoJSON format"""
    return jsonify({
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
                    'type': 'fire', 
                    'severity': 4,
                    'severity_score': 8.5,
                    'prank_confidence': 0.2,
                    'verified': True,
                    'caller_type': 'verified',
                    'address': 'Central Delhi, Connaught Place',
                    'reported_at': '2024-01-15T10:30:00',
                    'status': 'active'
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
                    'type': 'medical', 
                    'severity': 3,
                    'severity_score': 7.2,
                    'prank_confidence': 0.65,
                    'verified': False,
                    'caller_type': 'first_time',
                    'address': 'East Delhi, Preet Vihar',
                    'reported_at': '2024-01-15T11:15:00',
                    'status': 'active'
                }
            },
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point', 
                    'coordinates': [77.2290, 28.6099]
                },
                'properties': {
                    'id': 3,
                    'type': 'accident',
                    'severity': 5,
                    'severity_score': 9.1,
                    'prank_confidence': 0.15,
                    'verified': True,
                    'caller_type': 'emergency_services',
                    'address': 'South Delhi, Saket',
                    'reported_at': '2024-01-15T12:00:00',
                    'status': 'active'
                }
            },
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point', 
                    'coordinates': [77.2390, 28.5999]
                },
                'properties': {
                    'id': 4,
                    'type': 'fire',
                    'severity': 4,
                    'severity_score': 6.8,
                    'prank_confidence': 0.85,
                    'verified': False,
                    'caller_type': 'anonymous',
                    'address': 'North Delhi, Rohini',
                    'reported_at': '2024-01-15T13:30:00',
                    'status': 'active'
                }
            }
        ]
    })

@app.route('/api/resources')
def get_resources():
    """Get all resources"""
    return jsonify([
        {
            'id': 1, 
            'type': 'ambulance', 
            'status': 'available', 
            'location': [77.1990, 28.6039],
            'capacity': 4,
            'details': {'equipment': ['stretcher', 'oxygen']}
        },
        {
            'id': 2, 
            'type': 'fire_truck', 
            'status': 'available', 
            'location': [77.2290, 28.6339],
            'capacity': 6,
            'details': {'water_capacity': '5000L'}
        },
        {
            'id': 3, 
            'type': 'police', 
            'status': 'available', 
            'location': [77.1890, 28.5939],
            'capacity': 2,
            'details': {'officers': 2}
        },
        {
            'id': 4,
            'type': 'ambulance',
            'status': 'available',
            'location': [77.2390, 28.6439],
            'capacity': 2,
            'details': {'equipment': ['defibrillator']}
        }
    ])

@app.route('/api/resources/available')
def get_available_resources():
    """Get available resources in GeoJSON format"""
    return jsonify({
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
            },
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point', 
                    'coordinates': [77.2390, 28.6439]
                },
                'properties': {
                    'id': 4,
                    'type': 'ambulance',
                    'status': 'available',
                    'capacity': 2
                }
            }
        ]
    })

@app.route('/api/incidents/report', methods=['POST'])
def report_incident():
    """Report a new incident with severity scoring and prank detection"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Extract data with defaults
    incident_type = data.get('type', 'unknown')
    location = data.get('location', [77.2090, 28.6139])
    caller_id = data.get('caller_id', 'anonymous')
    caller_type = data.get('caller_type', 'anonymous')
    description = data.get('description', '')
    location_type = data.get('location_type', 'residential')
    address = data.get('address', 'Unknown location')
    
    # Get current time
    current_hour = datetime.now().hour
    is_peak_hours = (7 <= current_hour <= 10) or (16 <= current_hour <= 20)
    
    # 1. Calculate Severity Score
    severity_score = calculate_severity_score(
        incident_type=incident_type,
        call_count=get_call_count_nearby(location),
        location_type=location_type,
        time_factor=current_hour,
        historical_risk=get_historical_risk(location),
        caller_type=caller_type
    )
    
    # 2. Calculate Prank Confidence Score
    prank_confidence = calculate_prank_confidence(
        caller_id=caller_id,
        caller_type=caller_type,
        location=location,
        incident_type=incident_type,
        description=description,
        time_of_day=current_hour
    )
    
    # 3. Final Decision Logic
    is_verified = False
    verification_needed = False
    action_required = ''
    
    if prank_confidence < 0.3:  # High confidence it's real
        is_verified = True
        action_required = 'auto_dispatch'
    elif prank_confidence < 0.7:  # Medium confidence - needs verification
        verification_needed = True
        action_required = 'manual_verification'
    else:  # High confidence it's prank
        action_required = 'flag_for_review'
        # Log suspicious activity
        log_suspicious_activity(caller_id, location, incident_type)
    
    # Create incident record
    incident_id = random.randint(1000, 9999)
    
    response = {
        'message': 'Incident reported successfully',
        'incident_id': incident_id,
        'severity_score': round(severity_score, 1),
        'prank_confidence': round(prank_confidence, 2),
        'action_required': action_required,
        'verification_needed': verification_needed,
        'is_verified': is_verified,
        'estimated_response_time': calculate_response_time(severity_score, location),
        'details': {
            'severity_breakdown': {
                'incident_type_score': INCIDENT_TYPE_SCORES.get(incident_type, 5),
                'call_frequency_score': get_call_count_nearby(location) * 0.5,
                'location_risk_score': LOCATION_RISK_SCORES.get(location_type, 5),
                'time_factor_score': 8 if is_peak_hours else 5,
                'historical_risk_score': get_historical_risk(location),
                'caller_credibility_score': get_caller_credibility(caller_type)
            },
            'prank_detection_breakdown': {
                'caller_reputation': get_caller_reputation_score(caller_id, caller_type),
                'location_consistency': check_location_consistency(location, incident_type),
                'multi_call_verification': check_multi_call_verification(location),
                'time_pattern_analysis': analyze_time_pattern(caller_id, current_hour),
                'description_analysis': analyze_description(description)
            },
            'confidence': max(0, min(1, 1 - prank_confidence))  # Overall confidence (0-1)
        },
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(response), 201

@app.route('/api/routing/dispatch', methods=['POST'])
def dispatch_resource():
    """Dispatch a resource to an incident"""
    data = request.get_json()
    
    if not data or 'incident_id' not in data:
        return jsonify({'error': 'Missing incident_id'}), 400
    
    # Mock response - in real app, you would process this
    return jsonify({
        'message': 'Resource dispatched successfully',
        'dispatch_id': random.randint(1000, 9999),
        'incident_id': data.get('incident_id'),
        'resource_id': data.get('resource_id', 1),
        'estimated_arrival': f'{random.randint(5, 15)} minutes',
        'route_distance': f'{random.uniform(2.5, 8.7):.1f} km',
        'timestamp': datetime.now().isoformat()
    })

# Helper functions
def calculate_severity_score(incident_type, call_count, location_type, time_factor, historical_risk, caller_type):
    """Calculate comprehensive severity score using weighted factors"""
    
    # Normalize scores
    incident_score = INCIDENT_TYPE_SCORES.get(incident_type, 5) / 10.0
    call_score = min(call_count * 0.2, 1.0)  # Cap at 1.0
    location_score = LOCATION_RISK_SCORES.get(location_type, 5) / 10.0
    
    # Time factor: peak hours = higher severity
    is_peak = (7 <= time_factor <= 10) or (16 <= time_factor <= 20)
    time_score = 0.8 if is_peak else 0.5
    
    # Historical risk (0-1 scale)
    historical_score = historical_risk / 10.0
    
    # Caller credibility
    caller_credibility = get_caller_credibility(caller_type) / 10.0
    
    # Weighted sum with adjusted weights for new factor
    weights = {
        'incident_type': 0.25,
        'call_frequency': 0.15,
        'location_risk': 0.20,
        'time_factor': 0.15,
        'historical_data': 0.10,
        'caller_credibility': 0.15
    }
    
    severity = (
        weights['incident_type'] * incident_score +
        weights['call_frequency'] * call_score +
        weights['location_risk'] * location_score +
        weights['time_factor'] * time_score +
        weights['historical_data'] * historical_score +
        weights['caller_credibility'] * caller_credibility
    )
    
    # Convert to 1-10 scale
    return min(10, max(1, severity * 10))

def calculate_prank_confidence(caller_id, caller_type, location, incident_type, description, time_of_day):
    """Calculate confidence that incident is not a prank (0-1, higher = more likely real)"""
    
    confidence_factors = []
    
    # 1. Caller History Analysis
    caller_rep = get_caller_reputation_score(caller_id, caller_type)
    confidence_factors.append(caller_rep)
    
    # 2. Multi-Call Verification (simulated)
    multi_call_score = check_multi_call_verification(location)
    confidence_factors.append(multi_call_score)
    
    # 3. Location Consistency Check
    location_score = check_location_consistency(location, incident_type)
    confidence_factors.append(location_score)
    
    # 4. Time Pattern Analysis
    time_score = analyze_time_pattern(caller_id, time_of_day)
    confidence_factors.append(time_score)
    
    # 5. Description Analysis
    description_score = analyze_description(description)
    confidence_factors.append(description_score)
    
    # 6. Caller type credibility
    caller_type_score = get_caller_type_score(caller_type)
    confidence_factors.append(caller_type_score)
    
    # Average of all confidence factors
    avg_confidence = sum(confidence_factors) / len(confidence_factors)
    
    # Invert to get prank confidence (higher = more likely prank)
    return 1.0 - avg_confidence

def get_caller_reputation_score(caller_id, caller_type):
    """Get caller's reputation score (0-1)"""
    # Start with caller type base score
    base_scores = {
        'emergency_services': 0.95,
        'verified': 0.85,
        'first_time': 0.60,
        'anonymous': 0.30
    }
    
    score = base_scores.get(caller_type, 0.5)
    
    # Adjust based on history if available
    if caller_id in caller_history and caller_id != 'anonymous':
        history = caller_history[caller_id]
        false_reports = history.get('false_reports', 0)
        total_reports = history.get('total_reports', 1)
        
        if total_reports > 0:
            accuracy = 1.0 - (false_reports / total_reports)
            # Blend with base score
            score = (score + accuracy) / 2
    
    return max(0.1, min(0.99, score))

def get_caller_credibility(caller_type):
    """Get caller credibility score (1-10)"""
    scores = {
        'emergency_services': 9,
        'verified': 8,
        'first_time': 5,
        'anonymous': 3
    }
    return scores.get(caller_type, 5)

def get_caller_type_score(caller_type):
    """Get caller type confidence score (0-1)"""
    scores = {
        'emergency_services': 0.95,
        'verified': 0.85,
        'first_time': 0.60,
        'anonymous': 0.30
    }
    return scores.get(caller_type, 0.5)

def check_multi_call_verification(location):
    """Check if multiple calls from nearby locations (simulated)"""
    # Simulate: 70% chance of multi-call verification
    return 0.7 if random.random() > 0.3 else 0.3

def check_location_consistency(location, incident_type):
    """Check if incident type matches location (simulated)"""
    # In real app, query GIS database
    consistency_scores = {
        'fire': 0.8,
        'medical': 0.9,
        'medical_emergency': 0.9,
        'accident': 0.7,
        'flood': 0.6,
        'earthquake': 0.5,
        'explosion': 0.7,
        'building_collapse': 0.8
    }
    return consistency_scores.get(incident_type, 0.7)

def analyze_time_pattern(caller_id, current_hour):
    """Analyze if call pattern is suspicious"""
    # Odd hours (1-5 AM) are more suspicious
    if 1 <= current_hour <= 5:
        return 0.4  # Suspicious time
    
    # Normal hours (8 AM to 8 PM) are more reliable
    if 8 <= current_hour <= 20:
        return 0.9
    
    return 0.7  # Evening hours

def analyze_description(description):
    """Analyze description for authenticity"""
    if not description:
        return 0.5
    
    description_lower = description.lower()
    
    # Check for suspicious patterns
    suspicious_keywords = ['test', 'prank', 'just kidding', 'fake', 'not real', 'just testing']
    if any(keyword in description_lower for keyword in suspicious_keywords):
        return 0.2
    
    # Check for credible patterns
    credible_keywords = ['emergency', 'urgent', 'help', 'fire', 'accident', 'injured', 'bleeding', 'smoke']
    credible_count = sum(1 for keyword in credible_keywords if keyword in description_lower)
    
    # Longer, detailed descriptions are more credible
    word_count = len(description.split())
    
    # Calculate score based on word count and credible keywords
    if word_count > 30 and credible_count >= 2:
        return 0.95
    elif word_count > 20 and credible_count >= 1:
        return 0.85
    elif word_count > 10:
        return 0.70
    else:
        return 0.55

def get_call_count_nearby(location):
    """Get number of calls from nearby location in last 30 minutes (simulated)"""
    # Simulate: 1-5 calls
    return random.randint(1, 5)

def get_historical_risk(location):
    """Get historical risk score for location (simulated)"""
    # Use location to generate consistent but random-ish score
    lat, lng = location
    seed = int(lat * 10000 + lng * 10000)
    random.seed(seed)
    return random.uniform(3, 9)

def calculate_response_time(severity, location):
    """Calculate estimated response time based on severity"""
    base_time = 15  # minutes
    adjusted_time = base_time - (severity * 0.8)
    response_time = max(3, min(30, adjusted_time))
    return f"{response_time:.1f} minutes"

def log_suspicious_activity(caller_id, location, incident_type):
    """Log suspicious activity for review"""
    if caller_id not in caller_history:
        caller_history[caller_id] = {
            'false_reports': 0,
            'total_reports': 0,
            'call_times': [],
            'locations': []
        }
    
    caller_history[caller_id]['total_reports'] += 1
    caller_history[caller_id]['false_reports'] += 1
    caller_history[caller_id]['call_times'].append(datetime.now().hour)
    caller_history[caller_id]['locations'].append(location)

if __name__ == '__main__':
    print("=" * 60)
    print("🚨 AI-Powered Emergency Response System")
    print("=" * 60)
    print("🔹 Features:")
    print("   • Multi-factor Severity Scoring")
    print("   • Intelligent Prank Detection")
    print("   • Real-time Risk Assessment")
    print("   • Automated Verification System")
    print("\n🌐 Server: http://localhost:5000")
    print("\n📊 Available Endpoints:")
    print("   - GET  /                         - API Information")
    print("   - GET  /health                   - Health Check")
    print("   - GET  /api/incidents            - All incidents")
    print("   - GET  /api/incidents/active     - Active incidents (GeoJSON)")
    print("   - GET  /api/resources            - All resources")
    print("   - GET  /api/resources/available  - Available resources (GeoJSON)")
    print("   - POST /api/incidents/report     - Report new incident (with AI analysis)")
    print("   - POST /api/routing/dispatch     - Dispatch resource")
    print("\n✅ Frontend: Open frontend/index.html in browser")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)