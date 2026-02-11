from django.db import models
from django.contrib.auth.models import User

# Existing Profile model
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='profile_images/', default='profile_images/default.png')

    def __str__(self):
        return self.user.username


# 🌾 Community Post model
class CommunityPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Allow the user (author) to delete their own post
    def can_delete(self, user):
        return self.author == user  # Only author can delete their post

    def __str__(self):
        return self.title


# 💬 Comment model for discussions
class Comment(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Allow the user (author) to delete their own comment
    def can_delete(self, user):
        return self.author == user

    def __str__(self):
        return f"{self.author.username}: {self.text[:20]}"
