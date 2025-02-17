# serializers.py
from rest_framework import serializers
from .models import Post, PostPicture
from user.models import CustomUser  # Import your custom user model

class PostPictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostPicture
        fields = ['id', 'image', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser  # Use CustomUser model
        fields = ['username', 'first_name', 'last_name', 'profile_picture']  # Include relevant fields

class PostSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Add user details to the post
    pictures = PostPictureSerializer(many=True)  # Include related pictures

    class Meta:
        model = Post
        fields = ['id', 'user', 'text', 'created', 'updated', 'views', 'likes', 'pictures']
