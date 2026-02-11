from django.urls import path
from . import views

urlpatterns = [
    # ✅ Authentication
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # ✅ Main Pages
    path('home/', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('motor/', views.motor_view, name='motor'),
    
    # ✅ Sensor Data API Endpoint (for IoT devices to POST readings)
    path('sensor-data/', views.sensor_data_endpoint, name='sensor_data'),
    
    # Motor proxy endpoints (for local notification + proxy to external API)
    path('api/update-set/', views.motor_set_proxy, name='motor_set_proxy'),
    path('api/read/', views.motor_read_proxy, name='motor_read_proxy'),

    # ✅ New Navigation Pages
    path('contact-admin/', views.contact_admin_view, name='contact_admin'),
    path('contact-specialist/', views.contact_specialist_view, name='contact_specialist'),

    # ✅ Community Section (posts + comments + delete)
    path('community/', views.community_view, name='community'),
    path('community/add/', views.add_post_view, name='add_post'),
    path('community/comment/<int:post_id>/', views.add_comment_view, name='add_comment'),
    path('community/delete/<int:post_id>/', views.delete_post_view, name='delete_post'),
    path('community/comment/delete/<int:comment_id>/', views.delete_comment_view, name='delete_comment'),
    path('news/', views.agri_news, name='news'),
]

