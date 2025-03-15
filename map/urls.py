from django.urls import path
from .views import get_route, RouteView, map_view

urlpatterns = [
    path('api/map/route/', get_route, name='get_route'),
    path('route/', RouteView.as_view(), name='route'),
    path('', map_view, name='map'),
]