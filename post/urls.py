# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('posts/<str:username>/', views.PostByUsernameView.as_view(), name='posts-by-username'),
]
