# backend/app/services/flood_service.py
import numpy as np
from datetime import datetime
import random
import math

class FloodPredictor:
    def __init__(self):
        self.risk_thresholds = {
            'LOW': 0.3,
            'MODERATE': 0.5,
            'HIGH': 0.7,
            'CRITICAL': 0.9
        }
    
    def calculate_flood_risk(self, location, weather_data):
        """Calculate flood risk based on multiple factors"""
        
        # Extract factors
        rainfall = weather_data.get('rain', 0)
        humidity = weather_data.get('humidity', 50)
        
        # Calculate risk components
        rainfall_risk = min(1.0, rainfall / 100) * 0.4
        humidity_risk = (humidity / 100) * 0.2
        terrain_risk = self.get_terrain_risk(location) * 0.3
        historical_risk = self.get_historical_risk(location) * 0.1
        
        total_risk = rainfall_risk + humidity_risk + terrain_risk + historical_risk
        
        # Determine risk level
        risk_level = 'LOW'
        for level, threshold in self.risk_thresholds.items():
            if total_risk >= threshold:
                risk_level = level
        
        return {
            'risk_score': round(total_risk, 2),
            'risk_level': risk_level,
            'components': {
                'rainfall_risk': round(rainfall_risk, 2),
                'humidity_risk': round(humidity_risk, 2),
                'terrain_risk': round(terrain_risk, 2),
                'historical_risk': round(historical_risk, 2)
            }
        }
    
    def get_terrain_risk(self, location):
        """Get terrain-based risk (elevation, slope)"""
        # Mock terrain risk
        return random.uniform(0.3, 0.8)
    
    def get_historical_risk(self, location):
        """Get historical flood risk"""
        # Mock historical risk
        return random.uniform(0.2, 0.7)
    
    def generate_flood_zones(self, center_lat, center_lng, radius_km=10):
        """Generate flood risk zones for map display"""
        features = []
        
        for i in range(20):
            # Generate random points within radius
            lat = center_lat + (random.random() - 0.5) * 0.1
            lng = center_lng + (random.random() - 0.5) * 0.1
            
            # Calculate risk
            risk_score = random.uniform(0.2, 0.95)
            
            if risk_score > 0.5:  # Only include moderate to high risk
                features.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [lng, lat]
                    },
                    'properties': {
                        'risk_score': round(risk_score, 2),
                        'risk_level': self.get_risk_level(risk_score),
                        'area': f"{random.randint(1, 10)} km²",
                        'population_affected': random.randint(100, 10000)
                    }
                })
        
        return {
            'type': 'FeatureCollection',
            'features': features,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_risk_level(self, score):
        """Convert score to risk level"""
        if score >= 0.9:
            return 'CRITICAL'
        elif score >= 0.7:
            return 'HIGH'
        elif score >= 0.5:
            return 'MODERATE'
        else:
            return 'LOW'
    
    def predict_flood_inundation(self, location, water_level):
        """Predict flood inundation area"""
        lat, lng = location
        
        # Create simple flood polygon
        flood_radius = water_level * 100  # meters
        
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon',
                'coordinates': [[
                    [lng - 0.01, lat - 0.01],
                    [lng + 0.01, lat - 0.01],
                    [lng + 0.01, lat + 0.01],
                    [lng - 0.01, lat + 0.01],
                    [lng - 0.01, lat - 0.01]
                ]]
            },
            'properties': {
                'water_level': water_level,
                'area_affected': round(np.pi * flood_radius**2 / 1e6, 2),
                'risk_level': self.get_risk_level(water_level / 10)
            }
        }