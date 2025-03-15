import requests
from django.conf import settings
from math import radians, sin, cos, sqrt, atan2
import json, os

# Load Chennai Metro data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRO_DATA_PATH = os.path.join(BASE_DIR, 'map', 'data', 'chennai_metro.json')

with open(METRO_DATA_PATH, 'r', encoding="utf-8") as f:
    CHENNAI_METRO_DATA = json.load(f)

# Extract metro stations
METRO_STATIONS = [
    {
        "id": element['id'],
        "name": element['tags'].get('name', 'Unnamed Station'),
        "lat": element['lat'],
        "lon": element['lon'],
    }
    for element in CHENNAI_METRO_DATA['elements']
    if element['type'] == 'node' and 'railway' in element['tags']
]

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth.
    """
    R = 6371  # Earth radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c  # Distance in kilometers

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

def find_nearest_metro_station(lat, lon):
    """
    Find the nearest metro station to the given coordinates.
    """
    nearest_station = None
    min_distance = float('inf')
    
    for station in METRO_STATIONS:
        distance = haversine(lat, lon, station['lat'], station['lon'])
        if distance < min_distance:
            min_distance = distance
            nearest_station = station
    
    return nearest_station

def get_metro_route(start_station_id, end_station_id):
    """
    Get the metro route between two stations.
    """
    # Find the start and end stations
    start_station = next((station for station in METRO_STATIONS if station['id'] == start_station_id), None)
    end_station = next((station for station in METRO_STATIONS if station['id'] == end_station_id), None)
    
    if not start_station or not end_station:
        return {"error": "Invalid metro station IDs"}
    
    # Calculate distance and time between stations
    distance = haversine(start_station['lat'], start_station['lon'], end_station['lat'], end_station['lon'])
    time = distance * 3  # Assuming 3 minutes per km for metro
    
    return {
        "start_address": start_station['name'],
        "end_address": end_station['name'],
        "distance": distance * 1000,  # Convert to meters
        "time": time * 60,  # Convert to seconds
        "instructions": [{"text": f"Take metro from {start_station['name']} to {end_station['name']}", "distance": distance * 1000}],
        "paths": [{
            "points": {
                "coordinates": [
                    [start_station['lon'], start_station['lat']],
                    [end_station['lon'], end_station['lat']]
                ]
            }
        }]
    }

def get_graphhopper_route(start_lat, start_lng, end_lat, end_lng, vehicle='car'):
    """
    Fetch optimal route from Graphhopper Directions API.
    If vehicle is 'metro', use Chennai Metro data.
    """
    if vehicle == 'metro':
        # Find nearest metro stations
        start_station = find_nearest_metro_station(start_lat, start_lng)
        end_station = find_nearest_metro_station(end_lat, end_lng)
        
        if not start_station or not end_station:
            return {"error": "Could not find metro stations near the start or end location"}
        
        # Get route from start to metro station (car)
        car_to_metro = get_graphhopper_route(start_lat, start_lng, start_station['lat'], start_station['lon'], 'car')
        if 'error' in car_to_metro:
            return car_to_metro
        
        # Get metro route between stations
        metro_route = get_metro_route(start_station['id'], end_station['id'])
        if 'error' in metro_route:
            return metro_route
        
        # Get route from metro station to destination (car)
        metro_to_dest = get_graphhopper_route(end_station['lat'], end_station['lon'], end_lat, end_lng, 'car')
        if 'error' in metro_to_dest:
            return metro_to_dest
        
        # Combine routes
        return {
            "start_address": f"Start to {start_station['name']} (Car)",
            "end_address": f"{end_station['name']} to Destination (Car)",
            "distance": car_to_metro['distance'] + metro_route['distance'] + metro_to_dest['distance'],
            "time": car_to_metro['time'] + metro_route['time'] + metro_to_dest['time'],
            "instructions": car_to_metro['instructions'] + metro_route['instructions'] + metro_to_dest['instructions'],
            "paths": [car_to_metro['paths'][0], metro_route['paths'][0], metro_to_dest['paths'][0]],
        }
    
    # Default routing for car, bike, etc.
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