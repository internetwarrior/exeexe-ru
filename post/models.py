from django.db import models
from user.models import CustomUser as User
import uuid

class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)
    text = models.TextField(max_length=1000)
    likes = models.PositiveIntegerField(default=0)
    pictures = models.ManyToManyField('PostPicture', related_name='posts')

    def __str__(self):
        return f"Post {self.id}"

class PostPicture(models.Model):
    image = models.ImageField(upload_to='post_pictures/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Picture {self.id}"
