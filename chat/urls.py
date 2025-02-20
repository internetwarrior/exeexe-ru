from django.urls import path
from . import views


urlpatterns = [
    path('messages/<str:user_id>/', views.ChatHistoryView.as_view(), name='message-history'),
    path('chatrooms/', views.get_chatrooms_by_user, name='get_chatrooms_by_user'),
    path('chatroom/', views.create_or_get_chat, name='get_or_create_chatroom'),
]
