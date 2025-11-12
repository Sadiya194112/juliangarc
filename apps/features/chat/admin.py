from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.features.chat.models import ChatRoom, Message


# ------------------------
# ChatRoom Admin
# ------------------------
@admin.register(ChatRoom)
class ChatRoomAdmin(ModelAdmin):
    list_display = ('id', 'driver', 'host', 'created_at', 'chat_status')
    search_fields = ('driver__username', 'host__username')
    list_filter = ('created_at',)
    list_per_page = 25  # To limit the number of rows per page

    # Adding a custom field to show if the chat is active
    def chat_status(self, obj):
        return "Active" if obj.host and obj.driver else "Inactive"
    chat_status.short_description = "Chat Status"
    chat_status.admin_order_field = "host"  # Allow sorting by status
    
    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Driver", "sortable": True},
                {"name": "Host", "sortable": True},
                {"name": "Status", "sortable": True},
                {"name": "Created", "sortable": True},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Chat Room Details",
            "layout": [
                ("driver", "host"),
                ("created_at",),
            ],
            "save_button": "Save Chat Room",
        },
        "buttons": [
            {"name": "Add Chat Room", "icon": "plus", "url": "chatroom:add"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config


# ------------------------
# Message Admin
# ------------------------
@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'text', 'timestamp', 'message_preview')
    search_fields = ('sender__username', 'text')
    list_filter = ('timestamp',)
    list_per_page = 25

    # Adding a column to show a message preview
    def message_preview(self, obj):
        return obj.text[:50]  # Preview first 50 characters of the message text
    message_preview.short_description = "Message Preview"
    
    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Chat", "sortable": True},
                {"name": "Sender", "sortable": True},
                {"name": "Message Preview", "sortable": False},
                {"name": "Timestamp", "sortable": True},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Message Details",
            "layout": [
                ("sender", "chat"),
                ("text",),
                ("timestamp",),
            ],
            "save_button": "Save Message",
        },
        "buttons": [
            {"name": "Add Message", "icon": "plus", "url": "message:add"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config
