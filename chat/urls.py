from django.urls import path
from . import views


urlpatterns = [
    path('messages/<str:chat_name>/', views.get_messages_by_chat_name, name='get_messages_by_chat_name'),
    path('chatrooms/', views.get_chatrooms_by_user, name='get_chatrooms_by_user'),
]
