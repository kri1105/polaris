# map/views.py
from django.http import JsonResponse
from django.views import View
from .services import get_graphhopper_route
from django.shortcuts import render

def map_view(request):
    return render(request, 'map.html')

class RouteView(View):
    def get(self, request):
        # Get parameters from request
        start_lat = request.GET.get('start_lat', 48.23424)  # Default Munich coordinates
        start_lng = request.GET.get('start_lng', 11.58911)
        end_lat = request.GET.get('end_lat', 48.13743)      # Default Munich to Nuremberg
        end_lng = request.GET.get('end_lng', 11.57549)
        vehicle = request.GET.get('vehicle', 'car')
        
        route_data = get_graphhopper_route(
            float(start_lat),
            float(start_lng),
            float(end_lat),
            float(end_lng),
            vehicle
        )
        
        if 'error' in route_data:
            return JsonResponse({
                "status": "error",
                "message": route_data['error']
            }, status=400)
            
        # Process successful response
        main_path = route_data['paths'][0]
        return JsonResponse({
            "distance": main_path.get('distance', 0),  # in meters
            "time": main_path.get('time', 0),          # in milliseconds
            "points": main_path.get('points', {}).get('coordinates', []),
            "instructions": [
                {
                    "text": instr.get('text', ''),
                    "distance": instr.get('distance', 0),
                    "time": instr.get('time', 0)
                } for instr in main_path.get('instructions', [])
            ]
        })