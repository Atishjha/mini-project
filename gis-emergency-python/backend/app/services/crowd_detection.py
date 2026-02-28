# backend/app/services/crowd_detection.py
import numpy as np
from datetime import datetime, timedelta
import random
import base64
import json
from PIL import Image
from io import BytesIO
import math

# Import database models
from app.models.database import db
from app.models.crowd import CrowdLocation, CrowdData

class CrowdDetector:
    def __init__(self):
        self.thresholds = {
            'LOW': 50,
            'MODERATE': 100,
            'HIGH': 200,
            'CRITICAL': 300
        }
        
        # Density thresholds (people per square meter)
        self.density_thresholds = {
            'LOW': 0.5,
            'MODERATE': 1.5,
            'HIGH': 3.0,
            'CRITICAL': 5.0
        }
    
    def process_image(self, image_source):
        """Process image from file, URL, or base64"""
        try:
            if isinstance(image_source, str):
                if image_source.startswith('data:image'):
                    # Base64 encoded image
                    img_data = base64.b64decode(image_source.split(',')[1])
                    img = Image.open(BytesIO(img_data))
                    return img
                elif image_source.startswith('http'):
                    # URL - would need to download in production
                    return Image.new('RGB', (640, 480), color='gray')
                else:
                    # Local file path
                    return Image.open(image_source)
            
            return image_source if isinstance(image_source, Image.Image) else Image.new('RGB', (640, 480), color='white')
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return Image.new('RGB', (640, 480), color='white')
    
    def estimate_density(self, image, area_sq_meters=None):
        """
        Estimate crowd density from image
        In production, this would use a proper ML model like YOLO, MCNN, etc.
        """
        # Mock density estimation with some intelligence
        # Simulate different crowd densities based on image "complexity"
        
        # Convert image to grayscale and get basic stats for pseudo-randomness
        if image.mode != 'L':
            gray_img = image.convert('L')
        else:
            gray_img = image
        
        # Get image statistics for seed
        img_array = np.array(gray_img)
        mean_brightness = np.mean(img_array)
        std_brightness = np.std(img_array)
        
        # Use image stats to seed random but make it deterministic per image
        random.seed(int(mean_brightness * 100 + std_brightness))
        
        # Generate estimated count based on "image complexity"
        # Brighter images with higher std might indicate more complex scenes
        base_count = int(mean_brightness / 2 + std_brightness * 3)
        estimated_count = max(10, min(1000, base_count + random.randint(-50, 50)))
        
        # Calculate density if area provided
        density = estimated_count / area_sq_meters if area_sq_meters else None
        
        # Determine crowd level
        crowd_level = self.get_crowd_level(estimated_count)
        
        # Create density map (simplified - in production would be actual heatmap)
        density_map = self._create_density_map(estimated_count, image.size)
        
        # Reset random seed
        random.seed()
        
        return {
            'estimated_count': estimated_count,
            'crowd_level': crowd_level,
            'density': density,
            'density_map': density_map,
            'confidence': random.uniform(0.75, 0.95),
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_density_map(self, count, image_size):
        """Create a simplified density map (mock)"""
        height, width = image_size[1], image_size[0]
        
        # Create a grid of density values (simplified)
        grid_size = 10
        density_grid = []
        
        for i in range(grid_size):
            row = []
            for j in range(grid_size):
                # Density proportional to count, with some spatial variation
                cell_density = (count / 500) * (0.5 + 0.5 * math.sin(i * j))
                row.append(min(1.0, cell_density))
            density_grid.append(row)
        
        return {
            'grid': density_grid,
            'resolution': grid_size,
            'max_density': count / 500
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
    
    def get_density_level(self, density):
        """Determine crowd level based on density (people/m²)"""
        if density < self.density_thresholds['LOW']:
            return 'LOW'
        elif density < self.density_thresholds['MODERATE']:
            return 'MODERATE'
        elif density < self.density_thresholds['HIGH']:
            return 'HIGH'
        else:
            return 'CRITICAL'
    
    def detect_anomalies(self, current_density, historical_data):
        """Detect crowd anomalies using statistical methods"""
        if len(historical_data) < 5:
            return {'anomaly': False, 'message': 'Insufficient data'}
        
        recent = historical_data[-5:]
        mean = np.mean(recent)
        std = np.std(recent)
        
        # Detect rapid increase
        if current_density > mean + 2.5 * std:
            return {
                'anomaly': True,
                'type': 'RAPID_INCREASE',
                'severity': 'HIGH',
                'message': f'Critical crowd surge: +{(current_density/mean - 1)*100:.0f}% increase',
                'threshold': mean + 2.5 * std
            }
        elif current_density > mean + 1.5 * std:
            return {
                'anomaly': True,
                'type': 'MODERATE_INCREASE',
                'severity': 'MEDIUM',
                'message': f'Unusual crowd increase: +{(current_density/mean - 1)*100:.0f}%',
                'threshold': mean + 1.5 * std
            }
        
        # Detect rapid decrease (could indicate evacuation or incident)
        if current_density < mean - 2.5 * std:
            return {
                'anomaly': True,
                'type': 'RAPID_DECREASE',
                'severity': 'HIGH',
                'message': f'Sudden crowd dispersal: -{(1 - current_density/mean)*100:.0f}%',
                'threshold': mean - 2.5 * std
            }
        
        return {'anomaly': False}
    
    def estimate_risk_level(self, crowd_level, is_anomalous, time_of_day=None):
        """Estimate overall risk based on crowd factors"""
        risk_scores = {
            'LOW': 1,
            'MODERATE': 2,
            'HIGH': 3,
            'CRITICAL': 4
        }
        
        base_risk = risk_scores.get(crowd_level, 1)
        
        # Anomalies increase risk
        if is_anomalous:
            base_risk += 1
        
        # Time of day factor (evenings/weekends higher risk)
        if time_of_day:
            hour = time_of_day.hour if isinstance(time_of_day, datetime) else time_of_day
            if hour in range(17, 22):  # 5 PM to 10 PM
                base_risk += 0.5
            elif hour in range(22, 24) or hour in range(0, 5):  # Late night
                base_risk += 0.8
        
        # Map back to level
        if base_risk >= 4.5:
            return 'CRITICAL'
        elif base_risk >= 3.5:
            return 'HIGH'
        elif base_risk >= 2.5:
            return 'MODERATE'
        else:
            return 'LOW'


class CrowdMonitor:
    def __init__(self):
        self.locations = {}
        self.detector = CrowdDetector()
        
        # Try to load existing locations from database
        self._load_locations_from_db()
    
    def _load_locations_from_db(self):
        """Load crowd locations from database"""
        try:
            locations = CrowdLocation.query.filter_by(is_active=True).all()
            for loc in locations:
                # Get coordinates
                coords = None
                if loc.location:
                    from sqlalchemy import text
                    result = db.session.execute(
                        text(f"SELECT ST_X(location) as lng, ST_Y(location) as lat FROM crowd_locations WHERE id = {loc.id}")
                    ).first()
                    if result:
                        coords = {'lat': result[1], 'lng': result[0]}
                
                self.locations[loc.location_id] = {
                    'id': loc.id,
                    'source': loc.camera_source,
                    'history': [],
                    'alerts': [],
                    'last_update': None,
                    'current_count': 0,
                    'name': loc.name,
                    'lat': coords['lat'] if coords else 28.6139,
                    'lng': coords['lng'] if coords else 77.2090,
                    'is_active': loc.is_active,
                    'db_id': loc.id
                }
            print(f"Loaded {len(locations)} crowd locations from database")
        except Exception as e:
            print(f"Could not load locations from database: {e}")
    
    def add_camera_source(self, location_id, source_url, name="", lat=None, lng=None, save_to_db=True):
        """Add a camera source for monitoring"""
        
        # Create location in memory
        self.locations[location_id] = {
            'source': source_url,
            'history': [],
            'alerts': [],
            'last_update': None,
            'current_count': 0,
            'name': name,
            'lat': lat or 28.6139 + (hash(location_id) % 100) / 1000,
            'lng': lng or 77.2090 + (hash(location_id) % 100) / 1000,
            'is_active': True,
            'db_id': None
        }
        
        # Save to database if requested
        if save_to_db:
            try:
                from sqlalchemy import text
                
                # Create PostGIS point
                wkt = f'POINT({self.locations[location_id]["lng"]} {self.locations[location_id]["lat"]})'
                point = db.session.execute(
                    text(f"SELECT ST_GeomFromText('{wkt}', 4326)")
                ).scalar()
                
                crowd_loc = CrowdLocation(
                    location_id=location_id,
                    name=name,
                    location=point,
                    camera_source=source_url,
                    is_active=True
                )
                db.session.add(crowd_loc)
                db.session.commit()
                
                self.locations[location_id]['db_id'] = crowd_loc.id
                print(f"Saved crowd location {location_id} to database")
                
            except Exception as e:
                print(f"Error saving to database: {e}")
                db.session.rollback()
        
        return {'status': 'success', 'location_id': location_id}
    
    def monitor_camera(self, location_id, area_sq_meters=None):
        """Monitor a single camera feed and save to database"""
        if location_id not in self.locations:
            return {'error': 'Location not found'}
        
        location = self.locations[location_id]
        
        # Mock monitoring with realistic variation
        base_count = 100
        if location['history']:
            # Gradual change from previous value
            prev = location['history'][-1]
            change = random.randint(-20, 20)
            count = max(10, prev + change)
        else:
            # Random initial value
            count = random.randint(50, 300)
        
        location['history'].append(count)
        if len(location['history']) > 50:  # Keep last 50 readings
            location['history'] = location['history'][-50:]
        
        location['current_count'] = count
        location['last_update'] = datetime.now()
        
        crowd_level = self.detector.get_crowd_level(count)
        anomaly = self.detector.detect_anomalies(count, location['history'])
        
        if anomaly['anomaly']:
            location['alerts'].append({
                'timestamp': datetime.now().isoformat(),
                'message': anomaly['message'],
                'severity': anomaly['severity'],
                'count': count
            })
        
        # Calculate density if area provided
        density = count / area_sq_meters if area_sq_meters else count / 100  # Assume 100 sq m default
        
        # Save to database if location has DB ID
        if location.get('db_id'):
            try:
                crowd_data = CrowdData(
                    crowd_location_id=location['db_id'],
                    estimated_count=count,
                    crowd_level=crowd_level,
                    density_map={'grid': []},  # Simplified
                    is_anomaly=anomaly['anomaly'],
                    anomaly_type=anomaly.get('type') if anomaly['anomaly'] else None
                )
                db.session.add(crowd_data)
                db.session.commit()
            except Exception as e:
                print(f"Error saving crowd data: {e}")
                db.session.rollback()
        
        return {
            'location_id': location_id,
            'name': location['name'],
            'current_count': count,
            'crowd_level': crowd_level,
            'density': round(density, 2),
            'anomaly': anomaly,
            'history': location['history'][-10:],
            'timestamp': datetime.now().isoformat()
        }
    
    def monitor_all_cameras(self):
        """Monitor all active cameras"""
        results = []
        for loc_id in self.locations:
            if self.locations[loc_id]['is_active']:
                result = self.monitor_camera(loc_id)
                if 'error' not in result:
                    results.append(result)
        return results
    
    def get_heatmap_data(self):
        """Get crowd density heatmap data"""
        heatmap_data = []
        
        for loc_id, location in self.locations.items():
            if location['is_active']:
                heatmap_data.append({
                    'lat': location['lat'],
                    'lng': location['lng'],
                    'intensity': min(1.0, location['current_count'] / 500),
                    'count': location['current_count'],
                    'location_id': loc_id,
                    'name': location['name']
                })
        
        return heatmap_data
    
    def get_geojson(self):
        """Get crowd data in GeoJSON format"""
        features = []
        
        for loc_id, location in self.locations.items():
            if location['is_active']:
                crowd_level = self.detector.get_crowd_level(location['current_count'])
                risk_level = self.detector.estimate_risk_level(
                    crowd_level, 
                    any(a['severity'] == 'HIGH' for a in location['alerts'][-5:]),
                    location['last_update']
                )
                
                # Check for recent anomalies
                recent_anomalies = [a for a in location['alerts'][-3:] if a['severity'] in ['HIGH', 'MEDIUM']]
                is_anomalous = len(recent_anomalies) > 0
                
                features.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [location['lng'], location['lat']]
                    },
                    'properties': {
                        'id': loc_id,
                        'address': location['name'] or f"Location {loc_id}",
                        'place_type': self._infer_place_type(location['name']),
                        'estimated_crowd_size': location['current_count'],
                        'crowd_density': crowd_level.lower(),
                        'density_score': location['current_count'] / 500,
                        'detection_source': 'camera',
                        'detection_confidence': 0.85 + (random.random() * 0.1),
                        'is_anomalous': is_anomalous,
                        'anomaly_type': recent_anomalies[0]['type'] if recent_anomalies else None,
                        'risk_level': risk_level.lower(),
                        'detected_at': location['last_update'].isoformat() if location['last_update'] else datetime.now().isoformat(),
                        'event': self._infer_event(location['name'], crowd_level)
                    }
                })
        
        return {
            'type': 'FeatureCollection',
            'features': features
        }
    
    def _infer_place_type(self, name):
        """Infer place type from name"""
        name_lower = (name or '').lower()
        if any(word in name_lower for word in ['market', 'bazaar', 'mall', 'shop']):
            return 'commercial'
        elif any(word in name_lower for word in ['stadium', 'ground', 'park', 'field']):
            return 'open_field'
        elif any(word in name_lower for word in ['station', 'airport', 'bus']):
            return 'transit'
        elif any(word in name_lower for word in ['temple', 'mosque', 'church']):
            return 'religious'
        else:
            return 'public_area'
    
    def _infer_event(self, name, crowd_level):
        """Infer if there might be an event"""
        name_lower = (name or '').lower()
        if crowd_level in ['HIGH', 'CRITICAL']:
            if any(word in name_lower for word in ['stadium', 'ground']):
                return 'sports_event'
            elif any(word in name_lower for word in ['temple', 'mosque']):
                return 'religious_gathering'
            elif any(word in name_lower for word in ['market', 'bazaar']):
                return 'market_day'
        return None
    
    def get_location_history(self, location_id, hours=24):
        """Get historical data for a location"""
        if location_id not in self.locations:
            return {'error': 'Location not found'}
        
        location = self.locations[location_id]
        
        # If we have DB ID, try to get from database
        if location.get('db_id'):
            try:
                cutoff = datetime.now() - timedelta(hours=hours)
                data = CrowdData.query.filter_by(
                    crowd_location_id=location['db_id']
                ).filter(
                    CrowdData.timestamp >= cutoff
                ).order_by(CrowdData.timestamp).all()
                
                return [{
                    'timestamp': d.timestamp.isoformat(),
                    'count': d.estimated_count,
                    'level': d.crowd_level,
                    'is_anomaly': d.is_anomaly,
                    'anomaly_type': d.anomaly_type
                } for d in data]
            except Exception as e:
                print(f"Error fetching history: {e}")
        
        # Fallback to in-memory history
        timestamps = []
        for i, count in enumerate(location['history'][-hours:]):
            timestamps.append({
                'timestamp': (datetime.now() - timedelta(minutes=len(location['history'])-i)).isoformat(),
                'count': count,
                'level': self.detector.get_crowd_level(count),
                'is_anomaly': False
            })
        return timestamps
