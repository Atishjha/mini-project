import requests
import json
from geopy.distance import geodesic
from app.models.database import db, Resource, Incident
from app.utils.gis_utils import calculate_distance

class RoutingService:
    def __init__(self, api_key=None):
        self.base_url = "https://api.openrouteservice.org/v2"
        self.api_key = api_key or "your-api-key"
        
    def find_optimal_route(self, start_coords, end_coords, profile='driving-car'):
        """Get optimal route using OpenRouteService"""
        url = f"{self.base_url}/directions/{profile}"
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        
        body = {
            "coordinates": [start_coords, end_coords],
            "instructions": False,
            "geometry": True
        }
        
        try:
            response = requests.post(url, json=body, headers=headers)
            data = response.json()
            
            if response.status_code == 200:
                route = data['routes'][0]
                return {
                    'distance': route['summary']['distance'],  # meters
                    'duration': route['summary']['duration'],  # seconds
                    'geometry': route['geometry']
                }
        except Exception as e:
            print(f"Routing error: {e}")
            return self.fallback_route(start_coords, end_coords)
    
    def fallback_route(self, start_coords, end_coords):
        """Fallback route calculation using haversine distance"""
        start_lat, start_lon = start_coords
        end_lat, end_lon = end_coords
        
        # Calculate straight-line distance
        distance_km = geodesic((start_lat, start_lon), (end_lat, end_lon)).kilometers
        
        # Estimate time (assuming average speed of 40 km/h in urban areas)
        estimated_time_min = (distance_km / 40) * 60
        
        return {
            'distance': distance_km * 1000,  # Convert to meters
            'duration': estimated_time_min * 60,  # Convert to seconds
            'geometry': None
        }
    
    def find_nearest_resources(self, incident_location, resource_type=None, limit=3):
        """Find nearest available resources to incident"""
        # Convert incident location to WKT for PostGIS query
        incident_wkt = f"POINT({incident_location[1]} {incident_location[0]})"
        
        # Build query
        query = Resource.query.filter(Resource.status == 'available')
        
        if resource_type:
            query = query.filter(Resource.resource_type == resource_type)
        
        # Add distance calculation using PostGIS
        query = query.add_columns(
            db.func.ST_Distance(
                Resource.current_location,
                db.func.ST_GeomFromText(incident_wkt, 4326)
            ).label('distance')
        ).order_by('distance').limit(limit)
        
        resources = []
        for resource, distance in query.all():
            resource_data = resource.to_geojson()
            resource_data['properties']['distance_km'] = distance / 1000  # Convert to km
            resources.append(resource_data)
        
        return resources