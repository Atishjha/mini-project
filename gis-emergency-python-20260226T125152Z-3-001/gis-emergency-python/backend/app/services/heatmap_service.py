# backend/app/services/heatmap_service.py
import numpy as np
from datetime import datetime
import random

# Don't import from models here - keep services independent
class HeatmapService:
    @staticmethod
    def generate_incident_heatmap(start_date=None, end_date=None, severity_min=1):
        """Generate heatmap data from incident locations"""
        
        # Mock data generation
        heatmap_data = []
        center_lat, center_lng = 28.6139, 77.2090  # Delhi coordinates
        
        # Generate 50 random points around Delhi
        for i in range(50):
            lat = center_lat + random.uniform(-0.1, 0.1)
            lng = center_lng + random.uniform(-0.1, 0.1)
            intensity = random.uniform(0.1, 1.0) * (severity_min / 10)
            
            heatmap_data.append([lat, lng, intensity])
        
        return {
            'type': 'heatmap',
            'data': heatmap_data,
            'count': len(heatmap_data),
            'metadata': {
                'start_date': start_date,
                'end_date': end_date,
                'severity_min': severity_min,
                'generated_at': datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def generate_crowd_heatmap(locations=None):
        """Generate crowd density heatmap"""
        heatmap_data = []
        
        # Mock crowd data
        for i in range(30):
            lat = 28.6139 + random.uniform(-0.08, 0.08)
            lng = 77.2090 + random.uniform(-0.08, 0.08)
            density = random.uniform(0.2, 1.0)
            
            heatmap_data.append({
                'lat': lat,
                'lng': lng,
                'intensity': density,
                'count': int(density * 500)
            })
        
        return heatmap_data