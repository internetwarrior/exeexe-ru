from django.urls import path
from .views import PasswordResetView, PasswordChangeView,RegisterView,verify_email,chat_view,UserProfileByUsernameView,CustomTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

from .views import UserProfileView,FriendsListView,FriendsRequestsListView

urlpatterns = [
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/<str:username>/', UserProfileByUsernameView.as_view(), name='user-profile-by-username'),

    path('friend/requests/',FriendsRequestsListView.as_view(),name='friends-requests'),
    path('friend/toggle_request/', views.send_cancel_friend_request, name='send_cancel_friend_request'),

    path('friends/<str:username>/', FriendsListView.as_view(), name='friends-list'),
    path('friends/check/<str:target_username>/', views.check_if_friends, name='check_if_friends'),

    path('register/', RegisterView.as_view(), name='register'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password-change/', PasswordChangeView.as_view(), name='password_change'),

    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('verify-email/', verify_email, name='verify_email'),
    path('chat/', chat_view, name='chat'),
]
