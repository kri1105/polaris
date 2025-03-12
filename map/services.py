# map/services.py
import requests
from django.conf import settings

def geocode_location(location_name):
    """
    Convert location name to coordinates using Graphhopper's Geocoding API.
    """
    endpoint = "https://graphhopper.com/api/1/geocode"
    params = {
        "q": location_name,  # Location name (e.g., "Chennai, India")
        "limit": 1,  # Return only the top result
        "key": settings.GRAPH_HOPPER_API_KEY,  # Your Graphhopper API key
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('hits'):
            return None  # No results found
            
        # Extract the first result
        first_result = data['hits'][0]
        return {
            "lat": first_result['point']['lat'],
            "lon": first_result['point']['lng'],
            "display_name": first_result.get('name', location_name),
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_graphhopper_route(start_lat, start_lng, end_lat, end_lng, vehicle='car'):
    """
    Fetch optimal route from Graphhopper Directions API.
    """
    endpoint = "https://graphhopper.com/api/1/route"
    params = {
        "point": [f"{start_lat},{start_lng}", f"{end_lat},{end_lng}"],
        "vehicle": vehicle,
        "locale": "en",
        "key": settings.GRAPH_HOPPER_API_KEY,
        "instructions": True,
        "calc_points": True,
        "points_encoded": False
    }
    
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'paths' not in data or not data['paths']:
            return {"error": "No route found"}
            
        return data
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    except KeyError as e:
        return {"error": f"Invalid response format: {str(e)}"}