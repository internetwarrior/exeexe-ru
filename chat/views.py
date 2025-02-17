from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from .models import ChatRoom, Message
from django.shortcuts import get_object_or_404


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField()
    timestamp = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Message
        fields = ['sender', 'content', 'timestamp', 'is_deleted_for_all']


class ChatRoomSerializer(serializers.ModelSerializer):
    participants = serializers.StringRelatedField(many=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = ChatRoom
        fields = ['name', 'created_at', 'participants']


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages_by_chat_name(request, chat_name):
    chat_room = get_object_or_404(ChatRoom, name=chat_name, participants=request.user)
    messages = Message.objects.filter(chat_room=chat_room).order_by('timestamp')
    
    # Filter visible messages
    visible_messages = [msg for msg in messages if msg.is_visible_to(request.user)]
    
    serializer = MessageSerializer(visible_messages, many=True)
    return Response({"messages": serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chatrooms_by_user(request):
    # Filter ChatRooms by participants, where the current user is part of the chat room
    chat_rooms = ChatRoom.objects.filter(participants=request.user)
    print('hello')
    # Serialize the chat rooms
    serializer = ChatRoomSerializer(chat_rooms, many=True)
    
    # Return the serialized data in a response
    return Response({"chat_rooms": serializer.data})
