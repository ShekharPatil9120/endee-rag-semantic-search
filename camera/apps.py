# camera/apps.py
from django.apps import AppConfig

class CameraConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'camera'

    def ready(self):
        # Do NOT start threads here
        pass
