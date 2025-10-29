from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from apps.features.chat.models import Message, ChatRoom



class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'text', 'image', 'location', 'timestamp']
    
    
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