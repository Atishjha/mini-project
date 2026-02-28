# backend/app/services/crowd_detection.py
import numpy as np
from datetime import datetime
import random
import base64
from PIL import Image
from io import BytesIO

class CrowdDetector:
    def __init__(self):
        self.thresholds = {
            'LOW': 50,
            'MODERATE': 100,
            'HIGH': 200,
            'CRITICAL': 300
        }
    
    def process_image(self, image_source):
        """Process image from file, URL, or base64"""
        # Mock processing - in real app, would use OpenCV
        if isinstance(image_source, str):
            if image_source.startswith('data:image'):
                # Base64 encoded image
                img_data = base64.b64decode(image_source.split(',')[1])
                img = Image.open(BytesIO(img_data))
                return img
        
        return Image.new('RGB', (640, 480), color='white')
    
    def estimate_density(self, image):
        """Estimate crowd density"""
        # Mock density estimation
        estimated_count = random.randint(20, 500)
        
        # Determine crowd level
        crowd_level = self.get_crowd_level(estimated_count)
        
        return {
            'estimated_count': estimated_count,
            'crowd_level': crowd_level,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_crowd_level(self, count):
        """Determine crowd level based on count"""
        if count < self.thresholds['LOW']:
            return 'LOW'
        elif count < self.thresholds['MODERATE']:
            return 'MODERATE'
        elif count < self.thresholds['HIGH']:
            return 'HIGH'
        else:
            return 'CRITICAL'
    
    def detect_anomalies(self, current_density, historical_data):
        """Detect crowd anomalies"""
        if len(historical_data) < 5:
            return {'anomaly': False, 'message': 'Insufficient data'}
        
        recent = historical_data[-5:]
        mean = np.mean(recent)
        std = np.std(recent)
        
        if current_density > mean + 2 * std:
            return {
                'anomaly': True,
                'type': 'RAPID_INCREASE',
                'severity': 'HIGH',
                'message': f'Crowd increased by {(current_density/mean - 1)*100:.1f}%'
            }
        
        return {'anomaly': False}

class CrowdMonitor:
    def __init__(self):
        self.locations = {}
        self.detector = CrowdDetector()
    
    def add_camera_source(self, location_id, source_url):
        """Add a camera source for monitoring"""
        self.locations[location_id] = {
            'source': source_url,
            'history': [],
            'alerts': [],
            'last_update': None,
            'current_count': 0
        }
        return {'status': 'success', 'location_id': location_id}
    
    def monitor_camera(self, location_id):
        """Monitor a single camera feed"""
        if location_id not in self.locations:
            return {'error': 'Location not found'}
        
        location = self.locations[location_id]
        
        # Mock monitoring
        count = random.randint(50, 300)
        location['history'].append(count)
        if len(location['history']) > 20:
            location['history'] = location['history'][-20:]
        
        location['current_count'] = count
        location['last_update'] = datetime.now()
        
        crowd_level = self.detector.get_crowd_level(count)
        anomaly = self.detector.detect_anomalies(count, location['history'])
        
        if anomaly['anomaly']:
            location['alerts'].append({
                'timestamp': datetime.now().isoformat(),
                'message': anomaly['message'],
                'severity': anomaly['severity']
            })
        
        return {
            'location_id': location_id,
            'current_count': count,
            'crowd_level': crowd_level,
            'anomaly': anomaly,
            'history': location['history'][-10:],
            'timestamp': datetime.now().isoformat()
        }
    
    def get_heatmap_data(self):
        """Get crowd density heatmap data"""
        heatmap_data = []
        
        for loc_id, location in self.locations.items():
            # Mock coordinates based on location_id hash
            lat = 28.6139 + (hash(loc_id) % 100) / 1000
            lng = 77.2090 + (hash(loc_id) % 100) / 1000
            
            heatmap_data.append({
                'lat': lat,
                'lng': lng,
                'intensity': min(1.0, location['current_count'] / 500),
                'count': location['current_count'],
                'location_id': loc_id
            })
        
        return heatmap_data