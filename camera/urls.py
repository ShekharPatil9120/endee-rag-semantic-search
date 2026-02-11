from django.urls import path
from .views import show_photos, edit_ip

urlpatterns = [
    path('photos/', show_photos, name='show_photos'),
    path('edit-ip/', edit_ip, name='edit_ip'),
]
