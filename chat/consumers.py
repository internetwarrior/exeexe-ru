import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings
from urllib.parse import parse_qs
from .models import Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token = params.get("token", [None])[0]

        if not token:
            await self.close(code=4002)  # No token provided
            return

        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            self.user = await database_sync_to_async(User.objects.get)(id=decoded_token["user_id"])
        except jwt.ExpiredSignatureError:
            await self.close(code=4000)  # Token expired
            return
        except jwt.InvalidTokenError:
            await self.close(code=4001)  # Invalid token
            return

        # Each user has their own private group
        self.room_group_name = f"user_{self.user.id}"

        # Add user to their WebSocket group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get("content")
        send_to_id = data.get("send_to")
        
        try:
            sender__ = await database_sync_to_async(User.objects.get)(username= self.user)
        except:
            return

        if not send_to_id or not message_content:
            return
        
        try:
            recipient = await database_sync_to_async(User.objects.get)(id=send_to_id)
        except User.DoesNotExist:
            return  # Handle chat room not found
        # Create and save message
        message = Message(
            sender=self.user,
            receiver=recipient,
            content=message_content
        )

        await database_sync_to_async(message.save)()

        send_to_group = f"user_{send_to_id}"

        # Send message only to the recipient's WebSocket group
        print(sender__.id)
        await self.channel_layer.group_send(
            send_to_group,
            {
                "type": "chat_message",
                "content": message_content,
                "sender": self.user.username,
                "goal":sender__.id,
            }
        )

        # Optionally, send message to the current room group if needed
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "content": message_content,
                "sender": self.user.username,
                'goal':'myself',
            }
        )




    async def chat_message(self, event):
        # Only the intended recipient receives this message
        print(event)
        await self.send(text_data=json.dumps({
            "content": event["content"],
            "sender": event["sender"],
            "goal":event['goal'],
        }))

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
