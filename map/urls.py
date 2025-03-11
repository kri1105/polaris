from django.urls import path
from .views import RouteView, map_view

urlpatterns = [
    path('route/', RouteView.as_view(), name='route'),
    path('', map_view, name='map'),
]