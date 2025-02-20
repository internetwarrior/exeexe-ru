from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from .models import ChatRoom, Message
from django.shortcuts import get_object_or_404
from user.models import CustomUser as User




class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField()
    receiver = serializers.StringRelatedField()
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "sender", "receiver", "content", "timestamp", "is_read"]

    def get_is_read(self, obj):
        request = self.context.get("request")
        return request.user in obj.read_by.all() if request else False

class ChatRoomSerializer(serializers.ModelSerializer):
    participants = serializers.StringRelatedField(many=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = ChatRoom
        fields = ['name', 'created_at', 'participants']


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Message
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        receiver = get_object_or_404(User, id=user_id)
        print(receiver)
        messages = Message.objects.filter(
            sender=request.user, receiver=receiver, is_deleted_for_all=False
        ).exclude(deleted_for=request.user) | Message.objects.filter(
            sender=receiver, receiver=request.user, is_deleted_for_all=False
        ).exclude(deleted_for=request.user)

        messages = messages.order_by("timestamp")

        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)



from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import ChatRoom
from rest_framework_simplejwt.tokens import AccessToken

@api_view(['POST'])
def create_or_get_chat(request):
    try:
        # Decode the JWT token to get the user information
        token = AccessToken(request.headers.get('Authorization').split()[1])
        main_user = token.payload.get('user_id')

        # Get the second user from the request body
        second_user_username = request.data.get('username')

        # Get the main user and the second user
        main_user_obj = User.objects.get(id=main_user)
        second_user_obj = User.objects.get(username=second_user_username)
        print(second_user_obj.username)
        print(main_user_obj.username)

        # Try to find an existing chat room with both users
        chat_room = ChatRoom.objects.filter(
    participants=main_user_obj
).filter(participants=second_user_obj).first()
        print(chat_room)
        if chat_room:
            # Return the name of the existing chat room
            return Response({"chat_name": chat_room.name}, status=status.HTTP_200_OK)

        # If no existing chat room, create a new one
        new_chat = ChatRoom.objects.create()
        new_chat.add_participant(main_user_obj)
        new_chat.add_participant(second_user_obj)

        return Response({"chat_name": new_chat.name}, status=status.HTTP_201_CREATED)

    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages_by_chat_name(request, chat_name):
    chat_room = get_object_or_404(ChatRoom, name=chat_name, participants=request.user)
    messages = Message.objects.filter(chat_room=chat_room).order_by('timestamp')
    
    # Filter visible messages
    visible_messages = [msg for msg in messages if msg.is_visible_to(request.user)]
    
    serializer = MessageSerializer(visible_messages, many=True)
    return Response({"messages": serializer.data})


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "profile_picture"]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chatrooms_by_user(request):
    users = User.objects.all()
    serializer = CustomUserSerializer(users, many=True)
    return Response({"users": serializer.data})

