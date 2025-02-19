from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.contrib import messages
from .serializers import PasswordResetSerializer, PasswordChangeSerializer, RegisterSerializer, UserProfileSerializer
from rest_framework import generics

from .models import CustomUser
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny 
from .models import Friendship
from .serializers import FriendSerializer
from django.contrib.auth import get_user_model
from django.db.models import Q  # Import Q here

from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Friendship
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework.permissions import IsAuthenticated



def chat_view(request):
    return render(request, 'user/chat.html')


User = get_user_model()


class FriendsRequestsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        # Fetch the list of friend requests where the user is the requester
        friendships = Friendship.objects.filter(user=request.user, user_approved=False, friend_approved=True)

        # Collect the friends from the friendships
        friends = []
        for friendship in friendships:
            friends.append(friendship.friend)

        # Serialize the list of friends (friend requests)
        serializer = FriendSerializer(friends, many=True)
        return Response(serializer.data)



class FriendsListView(APIView):
    permission_classes = [AllowAny]  # Allow any user to access this view

    def get(self, request, username, format=None):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch the list of friends where the user is either 'user' or 'friend' and both are approved
        friendships = Friendship.objects.filter(
            Q(user=user, user_approved=True, friend_approved=True) | 
            Q(friend=user, user_approved=True, friend_approved=True)
        )

        # Collect the friends from the friendships
        friends = []
        for friendship in friendships:
            if friendship.user == user:
                friends.append(friendship.friend)
            else:
                friends.append(friendship.user)

        # Serialize the list of friends
        serializer = FriendSerializer(friends, many=True)
        return Response(serializer.data)


@permission_classes([permissions.IsAuthenticated])
@api_view(['POST'])
def send_cancel_friend_request(request):
    target_username = request.data.get('target_username')  # Ensure this is received
    if not target_username:
        return Response({"detail": "Target username is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        target_user = get_user_model().objects.get(username=target_username)
    except get_user_model().DoesNotExist:
        return Response({"detail": "Target user not found."}, status=status.HTTP_404_NOT_FOUND)

    if target_user == request.user:
        return Response({"detail": "You cannot send a friend request to yourself."}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the friendship already exists
    friendship = Friendship.objects.filter(user=request.user, friend=target_user).first()

    if friendship:
        # Toggle the user_approved status (only toggle this, not friend_approved)
        friendship.user_approved = not friendship.user_approved
        friendship.save()

        return Response({"user_approved": friendship.user_approved}, status=status.HTTP_200_OK)

    # Create a new friendship request if it doesn't exist
    Friendship.objects.create(user=request.user, friend=target_user, user_approved=True, friend_approved=False)
    return Response({"user_approved": True}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_if_friends(request, target_username):
    try:
        # Get the target user
        target_user = get_user_model().objects.get(username=target_username)
        
        # Check if there's an existing friendship where the user is approved
        friendship = Friendship.objects.filter(user=request.user, friend=target_user).first()

        if friendship:
            # Check if the current user is approved in the friendship
            is_friend = friendship.user_approved
        else:
            is_friend = False

        return Response({"is_friend": is_friend}, status=status.HTTP_200_OK)

    except get_user_model().DoesNotExist:
        return Response({"detail": "Target user not found."}, status=status.HTTP_404_NOT_FOUND)

class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user  # Returns the currently authenticated user


class UserProfileByUsernameView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        username = self.kwargs["username"]
        return get_object_or_404(CustomUser, username=username)

class PasswordResetView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)  # Use CustomUser model
                token = default_token_generator.make_token(user)
                reset_link = f'http://example.com/reset-password/?token={token}&uid={user.pk}'
                send_mail(
                    'Password Reset',
                    f'Click here to reset your password: {reset_link}',
                    'from@example.com',
                    [email],
                )
                return Response({"detail": "Password reset link sent."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"detail": "User with this email does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            uid = request.data.get("uid")  # Get UID from request

            try:
                uid = urlsafe_base64_decode(uid).decode()
                user = User.objects.get(pk=uid)

                if default_token_generator.check_token(user, token):
                    user.set_password(serializer.validated_data['new_password'])
                    user.save()
                    return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)
                else:
                    return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"detail": "Invalid token or user does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def verify_email(request):
    uid = request.GET.get('uid')
    token = request.GET.get('token')

    try:
        uid = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=uid)

        if default_token_generator.check_token(user, token):
            user.email_verified = True
            user.save()
            messages.success(request, 'Your email has been verified!')
            return redirect('login')  # Redirect to login or another page
        else:
            messages.error(request, 'Invalid or expired token.')
            return redirect('register')  # Redirect to registration page or error page
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('register')


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"detail": "User registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
