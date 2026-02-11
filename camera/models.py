from django.db import models

class Photo(models.Model):
    image = models.ImageField(upload_to="photos/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

class CameraIP(models.Model):
    ip_address = models.CharField(max_length=100, default="http://10.249.11.206:8080")

    def __str__(self):
        return self.ip_address
