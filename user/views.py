from django.shortcuts import get_object_or_404, redirect, render
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.db.models import Q

from rest_framework import generics, permissions, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import CustomUser, FriendRequest, Friendship
from .serializers import (
    FriendSerializer,
    PasswordChangeSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)

def chat_view(request):
    return render(request, 'user/chat.html')


User = get_user_model()
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name','profile_picture',]


#Searching
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import CustomUser

class SearchUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"users": []})
        
        # Split query into words
        search_terms = query.split()
        
        # Create base query filter
        query_filter = Q()

        for term in search_terms:
            # Add filtering conditions for each term for username, first_name, and last_name
            query_filter |= Q(username__icontains=term) | Q(first_name__icontains=term) | Q(last_name__icontains=term)

        # Apply filter to the CustomUser model
        users = CustomUser.objects.filter(query_filter)
        
        # Serialize the result
        serializer = CustomUserSerializer(users, many=True)
        return Response({"users": serializer.data})






#Profile
@permission_classes([permissions.IsAuthenticated])
@api_view(['POST'])
def edit_profile(request):
    user = request.user
    data = request.data
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.username = data.get('username', user.username)
    user.birthdate = data.get('birthdate', user.birthdate)
    # user.birthday = data.get('birthday', user.birthday)

    user.save()
    return Response({"detail": "Profile updated successfully."}, status=status.HTTP_200_OK)





@permission_classes([permissions.IsAuthenticated])
@api_view(['POST'])
def edit_profile_picture(request):
    user = request.user
    profile_picture = request.FILES.get('profile_picture')
    
    if not profile_picture:
        return Response({"detail": "No profile picture provided."}, status=status.HTTP_400_BAD_REQUEST)

    user.profile_picture = profile_picture
    user.save()
    
    return Response({"detail": "Profile picture updated successfully."}, status=status.HTTP_200_OK)

from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed

@permission_classes([permissions.IsAuthenticated])
@api_view(['POST'])
def change_email_and_password(request):
    user = request.user
    data = request.data

    prev_password = data.get('password')
    new_email = data.get('email')
    new_password = data.get('new_password')

    if not prev_password:
        return Response({"detail": "Previous password is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Authenticate the user with the previous password
    if not authenticate(username=user.username, password=prev_password):
        raise AuthenticationFailed("Previous password is incorrect.")
    
    # Update the email if provided
    if new_email and new_email != user.email:
        user.email = new_email

    # Update the password if provided
    if new_password:
        user.set_password(new_password)
    
    # Save the changes
    user.save()

    return Response({"detail": "Email and/or password updated successfully."}, status=status.HTTP_200_OK)



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        login_field = attrs.get("username")
        password = attrs.get("password")
        user = CustomUser.objects.filter(Q(username=login_field) | Q(email=login_field)).first()

        if user and user.check_password(password):
            attrs["username"] = user.username
        else:
            raise serializers.ValidationError("No active account found with the given credentials")

        data = super().validate(attrs)
        data["username"] = user.username  # Include username in the response
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = CustomUserSerializer()
    to_user = CustomUserSerializer()

    class Meta:
        model = FriendRequest
        fields = ['friendship', 'from_user', 'to_user', 'status', 'created_at', 'updated_at']

class FriendsRequestsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        friend_requests = FriendRequest.objects.filter(to_user=request.user,status =None)

        serializer = FriendRequestSerializer(friend_requests, many=True)
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
    target_username = request.data.get('target_username')
    if not target_username:
        return Response({"detail": "Target username is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        target_user = get_user_model().objects.get(username=target_username)
    except get_user_model().DoesNotExist:
        return Response({"detail": "Target user not found."}, status=status.HTTP_404_NOT_FOUND)

    if target_user == request.user:
        return Response({"detail": "You cannot send a friend request to yourself."}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the friendship already exists
    friendship = Friendship.objects.filter(
        Q(user=request.user, friend=target_user) | Q(user=target_user, friend=request.user)
    ).first()

    if friendship:
        friend_request = FriendRequest.objects.filter(friendship=friendship,status = None, to_user = request.user).first()
        can_request = FriendRequest.objects.filter(friendship=friendship, from_user = request.user).first()
        print(can_request)
        if friendship.user == request.user:
            if friend_request:
                friend_request.status = True
                friend_request.save()
            elif (can_request and can_request.can_create_new_request() and friendship.friend_approved == False and friendship.user_approved == False) or (can_request is None and friendship.friend_approved == False and friendship.user_approved == False):
                FriendRequest.objects.create(from_user=request.user, to_user=target_user, friendship=friendship)
            friendship.user_approved = not friendship.user_approved
        elif friendship.friend == request.user:
            if friend_request:
                friend_request.status = True
                friend_request.save()
            elif ((can_request and can_request.can_create_new_request() and friendship.friend_approved == False and friendship.user_approved == False) or (can_request is None and friendship.friend_approved == False and friendship.user_approved == False)):
                FriendRequest.objects.create(from_user=request.user, to_user=target_user, friendship=friendship)

            friendship.friend_approved = not friendship.friend_approved
           
        else:
            return Response({"detail": "Unauthorized action."}, status=status.HTTP_403_FORBIDDEN)

        friendship.save()
        return Response({
            "user_approved": friendship.user_approved,
            "friend_approved": friendship.friend_approved
        }, status=status.HTTP_200_OK)

    # Create a new friendship request if it doesn't exist
    new_friendship = Friendship.objects.create(user=request.user, friend=target_user, user_approved=True, friend_approved=False)
    FriendRequest.objects.create(from_user = request.user, to_user=target_user , friendship = new_friendship)
    return Response({"user_approved": True}, status=status.HTTP_201_CREATED)


@permission_classes([permissions.IsAuthenticated])
@api_view(['POST'])
def cancel_friend_request(request):
    try:
        from_user = get_user_model().objects.get(username=request.data['target_username'])
    except get_user_model().DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    friend_request = FriendRequest.objects.filter(from_user=from_user, to_user=request.user, status=None).first()

    if not friend_request:
        return Response({"detail": "No pending friend request found."}, status=status.HTTP_404_NOT_FOUND)

    friend_request.status = False
    friend_request.save()
    return Response({"detail": "Friend request canceled."}, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_if_friends(request, target_username):
    try:
        # Get the target user
        target_user = get_user_model().objects.get(username=target_username)
        
        # Check if there's an existing friendship where the user is approved
        friendship = Friendship.objects.filter(
            Q(user=request.user, friend=target_user, user_approved=True) | 
            Q(friend=request.user, user=target_user, friend_approved=True)
        ).first()

        if friendship:
            is_friend = True
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
