from django.urls import path, include

urlpatterns = [
    path('api/map/', include('map.urls')),
]