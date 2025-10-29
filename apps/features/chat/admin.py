from django.contrib import admin
from apps.features.chat.models import ChatRoom, Message


class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'driver', 'host', 'created_at')
    search_fields = ('driver__username', 'host__username')
    list_filter = ('created_at',)

admin.site.register(ChatRoom, ChatRoomAdmin)


class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'text', 'timestamp')
    search_fields = ('sender__username', 'text')
    list_filter = ('timestamp',)   

admin.site.register(Message, MessageAdmin)
