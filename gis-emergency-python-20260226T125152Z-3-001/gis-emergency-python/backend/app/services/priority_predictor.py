# backend/app/services/priority_predictor.py
import numpy as np
from datetime import datetime
import random

class PriorityPredictor:
    def __init__(self):
        self.model = None
        self.feature_weights = {
            'type_score': 0.3,
            'location_risk': 0.25,
            'time_factor': 0.2,
            'caller_credibility': 0.15,
            'historical_risk': 0.1
        }
    
    def extract_features(self, incident_data):
        """Extract features for prediction"""
        
        # Incident type mapping
        type_scores = {
            'fire': 0.9, 'explosion': 1.0, 'earthquake': 1.0,
            'medical': 0.8, 'building_collapse': 0.9, 'accident': 0.7,
            'flood': 0.6, 'riot': 0.8, 'default': 0.5
        }
        
        features = {
            'type_score': type_scores.get(incident_data.get('type', 'default'), 0.5),
            'location_risk': self.calculate_location_risk(
                incident_data.get('lat', 28.6139),
                incident_data.get('lng', 77.2090)
            ),
            'time_factor': self.calculate_time_factor(incident_data.get('hour', datetime.now().hour)),
            'caller_credibility': incident_data.get('caller_credibility', 0.5),
            'historical_risk': incident_data.get('historical_risk', 0.5),
            'call_count': min(incident_data.get('call_count', 1) / 10, 1.0)
        }
        
        return features
    
    def calculate_location_risk(self, lat, lng):
        """Calculate risk based on location"""
        # Simple risk calculation based on coordinates
        risk = (abs(lat - 28.6139) + abs(lng - 77.2090)) / 0.2
        return min(1.0, max(0.1, risk))
    
    def calculate_time_factor(self, hour):
        """Calculate time-based risk factor"""
        # Peak hours = higher risk
        if (7 <= hour <= 10) or (16 <= hour <= 20):
            return 0.9
        elif (0 <= hour <= 5):
            return 0.4
        else:
            return 0.6
    
    def predict_priority(self, incident_data):
        """Predict priority for new incident (1-5 scale)"""
        
        features = self.extract_features(incident_data)
        
        # Calculate weighted score
        score = (
            self.feature_weights['type_score'] * features['type_score'] +
            self.feature_weights['location_risk'] * features['location_risk'] +
            self.feature_weights['time_factor'] * features['time_factor'] +
            self.feature_weights['caller_credibility'] * features['caller_credibility'] +
            self.feature_weights['historical_risk'] * features['historical_risk']
        )
        
        # Add call count bonus
        score += features['call_count'] * 0.1
        
        # Convert to 1-5 priority
        priority = int(score * 5)
        priority = max(1, min(5, priority))
        
        # Calculate confidence
        confidence = 0.7 + (random.random() * 0.2)
        
        return {
            'priority': priority,
            'confidence': round(confidence, 2),
            'features': features,
            'method': 'ml_model' if self.model else 'rule_based'
        }
    
    def train_model(self, historical_data):
        """Mock training function"""
        return {
            'accuracy': 0.85,
            'feature_importance': self.feature_weights,
            'samples': len(historical_data) if historical_data else 100
        }