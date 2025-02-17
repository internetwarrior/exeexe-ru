import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message
import jwt
from django.conf import settings

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Get JWT token from the headers
        token = self.scope.get("query_string", b"").decode().split('=')[-1]  # Extract token
        if token:
            try:
                # Decode the JWT token to get user info
                decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                self.user = await database_sync_to_async(User.objects.get)(id=decoded_token["user_id"])
            except jwt.ExpiredSignatureError:
                await self.close(code=4000)  # Token has expired
                return
            except jwt.InvalidTokenError:
                await self.close(code=4001)  # Invalid token
                return
        else:
            await self.close(code=4002)  # No token provided
            return

        # If the user is authenticated, proceed with connecting to the room
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data["content"]
        username = self.user.username  # Use the authenticated user’s username

        # Retrieve or create the chat room object
        try:
            chat_room = await database_sync_to_async(ChatRoom.objects.get)(name=self.room_name)
        except ChatRoom.DoesNotExist:
            return  # Handle chat room not found

        # Save the message to the database
        message = Message(
            chat_room=chat_room,
            sender=self.user,
            content=message_content
        )
        await database_sync_to_async(message.save)()

        # Send message to WebSocket group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "content": message_content,
                "sender": username,
            }
        )

    async def chat_message(self, event):
        message = event["content"]
        username = event["sender"]

        # Send message to WebSocket client
        await self.send(text_data=json.dumps({
            "content": message,
            "sender": username,
        }))
