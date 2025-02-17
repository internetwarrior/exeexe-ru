# views.py
from rest_framework import generics
from rest_framework.response import Response
from .models import Post
from .serializers import PostSerializer
from django.contrib.auth import get_user_model
from datetime import datetime

class PostByUsernameView(generics.ListAPIView):
    serializer_class = PostSerializer

    def get_queryset(self):
        username = self.kwargs['username']
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Post.objects.none()  # Return empty queryset if user does not exist

        # Filter posts by username
        queryset = Post.objects.filter(user=user)

        # Filter by start_date if provided
        if start_date:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
                queryset = queryset.filter(created__gte=start_date)
            except ValueError:
                pass  # Ignore invalid date format

        # Filter by end_date if provided
        if end_date:
            try:
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
                queryset = queryset.filter(created__lte=end_date)
            except ValueError:
                pass  # Ignore invalid date format

        # Order by the created date to get the newest posts first
        return queryset.order_by('-created')
