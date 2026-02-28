# backend/app/services/weather_service.py
from datetime import datetime, timedelta
import random

class WeatherService:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def get_current_weather(self, lat, lng):
        """Get current weather for coordinates"""
        
        # Mock weather data
        conditions = ['Clear', 'Clouds', 'Rain', 'Thunderstorm', 'Haze', 'Fog']
        
        return {
            'temperature': round(random.uniform(15, 35), 1),
            'feels_like': round(random.uniform(14, 38), 1),
            'humidity': random.randint(30, 90),
            'pressure': random.randint(980, 1020),
            'weather': random.choice(conditions),
            'description': f"{random.choice(conditions)} conditions",
            'wind_speed': round(random.uniform(0, 30), 1),
            'wind_direction': random.randint(0, 360),
            'clouds': random.randint(0, 100),
            'rain': round(random.uniform(0, 20) if random.random() > 0.7 else 0, 1),
            'visibility': random.randint(1000, 10000),
            'timestamp': datetime.now().isoformat(),
            'location': {'lat': lat, 'lng': lng}
        }
    
    def get_forecast(self, lat, lng, days=5):
        """Get weather forecast"""
        forecast = []
        conditions = ['Clear', 'Clouds', 'Rain', 'Thunderstorm']
        
        for i in range(days):
            date = (datetime.now() + timedelta(days=i)).date().isoformat()
            forecast.append({
                'date': date,
                'temperature': {
                    'min': round(random.uniform(15, 20), 1),
                    'max': round(random.uniform(28, 35), 1)
                },
                'weather': random.choice(conditions),
                'humidity': random.randint(40, 80),
                'wind_speed': round(random.uniform(5, 25), 1),
                'rain_probability': random.randint(0, 80)
            })
        
        return {
            'location': {'lat': lat, 'lng': lng},
            'forecast': forecast,
            'generated': datetime.now().isoformat()
        }