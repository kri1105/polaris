import requests
from django.conf import settings
from math import radians, sin, cos, sqrt, atan2
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

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
            logger.error(f"No results found for location: {location_name}")
            return None  # No results found
            
        # Extract the first result
        first_result = data['hits'][0]
        logger.debug(f"Geocoded location '{location_name}' to coordinates: {first_result['point']['lat']}, {first_result['point']['lng']}")
        return {
            "lat": first_result['point']['lat'],
            "lon": first_result['point']['lng'],
            "display_name": first_result.get('name', location_name),
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error geocoding location '{location_name}': {e}")
        return {"error": str(e)}

def get_car_route(start_lat, start_lng, end_lat, end_lng):
    """
    Fetch optimal car route from Graphhopper Directions API.
    """
    endpoint = "https://graphhopper.com/api/1/route"
    params = {
        "point": [f"{start_lat},{start_lng}", f"{end_lat},{end_lng}"],
        "vehicle": "car",  # Specify the vehicle type (car, bike, foot, etc.)
        "locale": "en",  # Language for instructions
        "key": settings.GRAPH_HOPPER_API_KEY,  # Your GraphHopper API key
        "instructions": True,  # Include turn-by-turn instructions
        "calc_points": True,  # Include geometry points for the route
        "points_encoded": False  # Return coordinates as latitude/longitude pairs
    }
    
    try:
        # Make the API request
        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        
        # Check if the response contains valid route data
        if 'paths' not in data or not data['paths']:
            logger.error("No route found")
            return {"error": "No route found"}
        
        # Extract relevant route information
        route = data['paths'][0]
        logger.debug(f"Car route from ({start_lat}, {start_lng}) to ({end_lat}, {end_lng}) is {route['distance']} meters and will take {route['time']} milliseconds")
        return {
            "distance": route['distance'],  # Distance in meters
            "time": route['time'] / 1000,  # Time in seconds (Graphhopper returns time in milliseconds)
            "instructions": route['instructions'],  # Turn-by-turn instructions
            "points": route['points'],  # Geometry of the route
            "paths": [{
                "points": {
                    "coordinates": route['points']['coordinates']  # Latitude/longitude pairs
                }
            }]
        }
        
    except requests.exceptions.RequestException as e:
        # Handle request errors
        logger.error(f"Error fetching car route: {e}")
        return {"error": str(e)}

def get_train_stations():
    """
    Fetch a list of train stations with their names, codes, and coordinates.
    This can be replaced with an API call or a database query.
    """
    # Example static data (replace with actual API or database call)
    stations = [
        {"name": "Potheri", "code": "POI", "lat": 12.8236, "lon": 80.0444},
        {"name": "Guindy", "code": "GY", "lat": 13.0067, "lon": 80.2206},
        {"name": "Chennai Central", "code": "MAS", "lat": 13.0827, "lon": 80.2707},
        # Add more stations as needed
    ]
    return stations

def get_nearest_station(lat, lon, stations):
    """
    Find the nearest train station from a given latitude and longitude.
    """
    nearest_station = None
    min_distance = float('inf')
    
    for station in stations:
        station_lat = station['lat']
        station_lon = station['lon']
        distance = haversine(lat, lon, station_lat, station_lon)
        if distance < min_distance:
            min_distance = distance
            nearest_station = station
    
    return nearest_station

def get_multi_modal_route(start_lat, start_lng, end_lat, end_lng):
    """
    Get a multi-modal route combining car and train.
    Automatically calculates the nearest stations for start and destination.
    """
    # Fetch train stations
    stations = get_train_stations()
    if not stations:
        return {"error": "No train stations available"}
    
    # Find nearest stations to start and end points
    start_station = get_nearest_station(start_lat, start_lng, stations)
    end_station = get_nearest_station(end_lat, end_lng, stations)
    
    if not start_station or not end_station:
        return {"error": "Could not find nearest stations"}
    
    # Get car route from start location to nearest station
    car_route_start = get_car_route(start_lat, start_lng, start_station['lat'], start_station['lon'])
    if 'error' in car_route_start:
        return car_route_start
    
    # Get car route from end station to destination
    car_route_end = get_car_route(end_station['lat'], end_station['lon'], end_lat, end_lng)
    if 'error' in car_route_end:
        return car_route_end
    
    # Combine routes
    combined_route = {
        "start_address": f"Start: {start_lat}, {start_lng}",
        "end_address": f"End: {end_lat}, {end_lng}",
        "distance": car_route_start['distance'] + car_route_end['distance'],
        "time": car_route_start['time'] + car_route_end['time'],
        "instructions": [
            *car_route_start['instructions'],
            {"text": f"Take train from {start_station['name']} to {end_station['name']}"},
            *car_route_end['instructions']
        ],
        "paths": [
            *car_route_start['paths'],
            *car_route_end['paths']
        ]
    }
    
    return combined_route