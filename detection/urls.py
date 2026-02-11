from django.urls import path
from . import views

urlpatterns = [
    path('', views.detection_home, name='detection_home'),  # detection home (under /detection/)
    path('upload_image/', views.upload_image, name='upload_image'),
    path('enter_url/', views.enter_url, name='enter_url'),
    
]
