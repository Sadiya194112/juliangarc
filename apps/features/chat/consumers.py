import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from apps.accounts.models import User
from apps.features.chat.models import ChatRoom, Message


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]
        chat_id = self.scope["url_route"]["kwargs"].get("chat_id")

        if not user.is_authenticated:
            await self.close()
            return

        chat_room = await self.get_chat(chat_id)
        if not chat_room:
            await self.close()
            return

        # Permission check (user must belong to the chat)
        allowed = await self.has_permission(user, chat_room)
        if not allowed:
            await self.close()
            return

        self.chat_id = chat_id
        self.room_group_name = f"chat_{chat_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.set_user_online(user)
        await self.accept()

        # Notify others about connection
        await self.broadcast_status(user, True)

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            await self.set_user_offline(user)
            await self.broadcast_status(user, False)

    async def receive(self, text_data: str):
        """Receive messages, store, and broadcast."""
        if not text_data:
            await self.send_json({"error": "Empty message payload."})
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json({"error": "Invalid JSON format."})
            return

        sender_id = data.get("sender_id")
        message_text = data.get("message")
        location = data.get("location")
        image = data.get("image")

        if not sender_id or not message_text:
            await self.send_json({"error": "Both sender_id and message are required."})
            return

        chat = await self.get_chat(self.chat_id)
        sender = await self.get_user(sender_id)

        # ✅ Save message (receiver determined automatically in model.save())
        msg = await self.create_message(chat, sender, message_text, location, image)

        # ✅ Serialize minimal message payload for broadcast
        message_data = {
            "id": msg.id,
            "chat_id": chat.id,
            "sender_id": sender.id,
            "receiver_id": msg.receiver.id if msg.receiver else None,
            "text": msg.text,
            "location": msg.location,
            "image": msg.image.url if msg.image else None,
            "timestamp": msg.timestamp.isoformat(),
        }

        # Broadcast to chat group
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "message": message_data}
        )

    async def chat_message(self, event):
        """Send message to WebSocket."""
        await self.send_json(event["message"])

    async def user_status(self, event):
        """Notify online/offline status updates."""
        await self.send_json(event)

    # ------------------------------------------------------------------
    # Database Utility Functions
    # ------------------------------------------------------------------
    @staticmethod
    @database_sync_to_async
    def get_chat(chat_id):
        try:
            return ChatRoom.objects.get(id=chat_id)
        except ChatRoom.DoesNotExist:
            return None

    @staticmethod
    @database_sync_to_async
    def get_user(user_id):
        return User.objects.get(id=user_id)

    @staticmethod
    @database_sync_to_async
    def create_message(chat, sender, text, location, image):
        return Message.objects.create(
            chat=chat, sender=sender, text=text, location=location, image=image
        )

    @database_sync_to_async
    def has_permission(self, user, chat_room):
        return chat_room.driver == user or chat_room.host == user

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
        """Broadcast when a user connects/disconnects."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user.status",
                "user_id": user.id,
                "is_online": online,
                "last_seen": None if online else timezone.now().isoformat(),
            },
        )

    # Helper for sending consistent JSON
    async def send_json(self, data):
        await self.send(text_data=json.dumps(data))
