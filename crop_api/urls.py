from django.urls import path
from .views import index, CropRecommendationAPI, get_live_sensor_data

urlpatterns = [
    path('', index, name='crop_api_home'),   # 👈 this name must match your template
    path('api/', CropRecommendationAPI.as_view(), name='crop_recommendation_api'),
    path('get-live-sensors/', get_live_sensor_data, name='get_live_sensors'),  # ✅ Proxy endpoint
]
