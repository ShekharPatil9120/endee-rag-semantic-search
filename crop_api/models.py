from django.db import models
from django.contrib.auth.models import User


class Recommendation(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	recommended_crop = models.CharField(max_length=100)
	possible_cultivation = models.TextField(blank=True)
	suggestions = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.recommended_crop} ({self.user.username})"
