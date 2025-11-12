from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from apps.features.chat.models import Message, ChatRoom



class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'chat', 'sender', 'receiver',
            'text', 'image', 'location', 'is_from_ai', 'timestamp'
        ]
    
    
class ChatRoomSerializer(serializers.ModelSerializer):
    driver = UserSerializer(read_only=True)
    host = UserSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'driver', 'host', 'created_at', 'last_message']

    def get_last_message(self, obj):
        message = obj.messages.last()
        return MessageSerializer(message).data if message else None