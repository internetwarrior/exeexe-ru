from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CustomUser

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'birthdate', 'profile_picture']


# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class FriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'profile_picture']  # Add any additional fields you want to show



class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordChangeSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()  # Use CustomUser model here
        fields = ['username', 'email', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords must match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = get_user_model().objects.create_user(**validated_data)  # Use CustomUser model
        return user
