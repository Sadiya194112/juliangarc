import json
from apps.accounts.models import User
from apps.features.chat.models import ChatRoom, Message
from channels.generic.websocket import AsyncWebsocketConsumer
from apps.features.chat.serializers import MessageSerializer
from channels.db import database_sync_to_async
from django.utils import timezone



class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        chat_id = self.scope["url_route"]["kwargs"].get("chat_id")

        if not user.is_authenticated:
            await self.close()
            return

        chat_room = await self.get_chat(chat_id)

        if not await self.has_permission(user, chat_room):
            await self.close()
            return

        self.chat_id = chat_id
        self.room_group_name = f"chat_{chat_id}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.set_user_online(user)
        await self.accept()
        
        # Notify others in chat about this user’s status
        await self.broadcast_status(user, True)

    async def disconnect(self, close_code):
        user = self.scope["user"]
        
        # Leave room group
        await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        await self.set_user_offline(user)
        
        # Notify others
        await self.broadcast_status(user, False)

    async def receive(self, text_data: str):
        if not text_data:
            await self.send(text_data=json.dumps({
                "message": "This field is required.",
                "sender_id": "This field is required."
            }))
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Invalid JSON format."
            }))
            return
        
        
        sender_id = data.get('sender_id')
        message_text = data.get('message')
        location = data.get('location', None)
        image = data.get('image', None)

        
        # Fetch chat and sender
        chat = await self.get_chat(self.chat_id)
        sender = await self.get_user(sender_id)

        # Save message to DB
        msg = await database_sync_to_async(Message.objects.create)(
            chat=chat,
            sender=sender,
            text=message_text,
            location=location,
            image=image
        )

        # Prepare message for broadcast
        message_data = {
            "id": msg.id,
            "chat_id": chat.id,
            "sender_id": sender.id,
            "text": msg.text,
            "location": msg.location,
            "image": msg.image.url if msg.image else None,
            "timestamp": msg.timestamp.isoformat()
        }

        # Broadcast to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event['message']))

    @staticmethod
    @database_sync_to_async
    def get_chat(chat_id):
        return ChatRoom.objects.get(id=chat_id)

    @staticmethod
    @database_sync_to_async
    def get_user(user_id):
        return User.objects.get(id=user_id)
    
    @database_sync_to_async
    def has_permission(self, user, chat_room):
        return (
            chat_room.driver == user or 
            chat_room.host == user
        )
        
    @database_sync_to_async
    def set_user_online(self, user):
        user.is_online = True
        user.save(update_fields=["is_online"])
        
    @database_sync_to_async
    def set_user_offline(self, user):
        user.is_online = False
        user.last_seen = timezone.now()
        user.save(update_fields=["is_online", "last_seen"])
        
    async def broadcast_status(self, user, online):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user.status",
                "user_id": user.id,
                "is_online": online,
                "last_seen": None if online else timezone.now().isoformat()
            }
        )

    async def user_status(self, event):
        await self.send(text_data=json.dumps(event))
