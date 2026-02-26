# backend/app/services/earthquake_service.py
from datetime import datetime, timedelta
import random

class EarthquakeService:
    def __init__(self):
        self.usgs_url = "https://earthquake.usgs.gov/fdsnws/event/1"
    
    def get_recent_earthquakes(self, min_magnitude=2.5, hours=24):
        """Get recent earthquakes"""
        
        # Mock earthquake data
        features = []
        
        # Generate random earthquakes
        for i in range(random.randint(1, 8)):
            magnitude = round(random.uniform(min_magnitude, min_magnitude + 2.5), 1)
            
            # Random location in Indian subcontinent
            lat = round(random.uniform(20, 35), 4)
            lng = round(random.uniform(70, 85), 4)
            
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [lng, lat]
                },
                'properties': {
                    'id': f'eq_{i}_{int(datetime.now().timestamp())}',
                    'magnitude': magnitude,
                    'place': self.get_place_name(lat, lng),
                    'time': (datetime.now() - timedelta(hours=random.randint(0, hours))).isoformat(),
                    'depth_km': round(random.uniform(5, 50), 1),
                    'tsunami_alert': magnitude > 7.0,
                    'significance': int(magnitude * 100)
                }
            })
        
        return {
            'type': 'FeatureCollection',
            'features': features,
            'count': len(features),
            'metadata': {
                'source': 'USGS (Mock)',
                'generated': datetime.now().isoformat()
            }
        }
    
    def get_place_name(self, lat, lng):
        """Get place name for coordinates"""
        places = {
            'North India': (30, 78),
            'Himalayas': (32, 77),
            'Delhi Region': (28.6, 77.2),
            'Gujarat': (23, 72),
            'Maharashtra': (19, 75),
            'Kashmir': (34, 76)
        }
        
        # Find closest place
        min_dist = float('inf')
        closest = 'Indian Subcontinent'
        
        for name, (place_lat, place_lng) in places.items():
            dist = abs(lat - place_lat) + abs(lng - place_lng)
            if dist < min_dist:
                min_dist = dist
                closest = name
        
        return closest
    
    def get_earthquake_alerts(self, region_bounds=None, min_magnitude=4.0):
        """Get earthquake alerts"""
        earthquakes = self.get_recent_earthquakes(min_magnitude, hours=48)
        alerts = []
        
        for feature in earthquakes['features']:
            props = feature['properties']
            coords = feature['geometry']['coordinates']
            
            # Check region bounds if specified
            if region_bounds:
                if not (region_bounds['min_lat'] <= coords[1] <= region_bounds['max_lat'] and
                        region_bounds['min_lng'] <= coords[0] <= region_bounds['max_lng']):
                    continue
            
            # Determine severity
            if props['magnitude'] >= 7.0:
                severity = 'CRITICAL'
                message = f"MAJOR EARTHQUAKE: M{props['magnitude']} near {props['place']}"
            elif props['magnitude'] >= 5.5:
                severity = 'HIGH'
                message = f"Strong earthquake: M{props['magnitude']} near {props['place']}"
            elif props['magnitude'] >= 4.0:
                severity = 'MEDIUM'
                message = f"Moderate earthquake: M{props['magnitude']} near {props['place']}"
            else:
                severity = 'LOW'
                message = f"Minor earthquake: M{props['magnitude']} near {props['place']}"
            
            alerts.append({
                'type': 'earthquake',
                'severity': severity,
                'message': message,
                'location': props['place'],
                'magnitude': props['magnitude'],
                'depth_km': props['depth_km'],
                'tsunami_risk': props['tsunami_alert'],
                'coordinates': [coords[1], coords[0]],
                'timestamp': props['time'],
                'id': props['id']
            })
        
        return alerts