from django.http import JsonResponse
from django.views import View
from .services import geocode_location, get_graphhopper_route

from django.shortcuts import render

def map_view(request):
    return render(request, 'map.html')


class RouteView(View):
    def get(self, request):
        # Get parameters from request
        start = request.GET.get('start', '')
        end = request.GET.get('end', '')
        vehicle = request.GET.get('vehicle', 'car')  # Default to car
        
        if not start or not end:
            return JsonResponse({"error": "Both start and end locations are required"}, status=400)
        
        try:
            # Geocode addresses
            start_geocode = geocode_location(start)
            end_geocode = geocode_location(end)
            
            if not start_geocode:
                return JsonResponse({"error": f"Could not geocode start location: {start}"}, status=400)
            if not end_geocode:
                return JsonResponse({"error": f"Could not geocode end location: {end}"}, status=400)
                
            # Get route data
            route_data = get_graphhopper_route(
                start_geocode['lat'],
                start_geocode['lon'],
                end_geocode['lat'],
                end_geocode['lon'],
                vehicle
            )
            
            if 'error' in route_data:
                return JsonResponse({"error": route_data['error']}, status=400)
                
            # Process successful response
            return JsonResponse({
                "start_address": start_geocode.get('display_name', start),
                "end_address": end_geocode.get('display_name', end),
                "distance": route_data.get('distance', 0),
                "time": route_data.get('time', 0),
                "instructions": route_data.get('instructions', []),
                "paths": route_data.get('paths', []),
            })
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)