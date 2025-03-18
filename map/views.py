from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_GET
from .services import geocode_location, get_multi_modal_route

from django.shortcuts import render

def map_view(request):
    return render(request, 'map.html')

@require_GET
def get_route(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    start_station_name = request.GET.get('start_station')
    end_station_name = request.GET.get('end_station')

    if not start or not end or not start_station_name or not end_station_name:
        return JsonResponse({'error': 'Missing required parameters'}, status=400)

    # Geocode start and end locations
    start_coords = geocode_location(start)
    end_coords = geocode_location(end)

    if not start_coords or not end_coords:
        return JsonResponse({'error': 'Could not geocode locations'}, status=400)

    # Get multi-modal route
    route = get_multi_modal_route(
        start_coords['lat'], start_coords['lon'],
        end_coords['lat'], end_coords['lon'],
        start_station_name, end_station_name
    )

    return JsonResponse(route)

class RouteView(View):
    def get(self, request):
        # Get parameters from request
        start = request.GET.get('start', '')
        end = request.GET.get('end', '')
        
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
                
            # Get multi-modal route data
            route_data = get_multi_modal_route(
                start_geocode['lat'],
                start_geocode['lon'],
                end_geocode['lat'],
                end_geocode['lon']
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