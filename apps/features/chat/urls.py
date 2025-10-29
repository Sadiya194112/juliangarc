from django.urls import path
from apps.features.chat.views import my_chats, create_chat, get_messages, ai_chat



urlpatterns = [
    path('my-chats/', my_chats, name='my_chats'),
    path('create/<int:host_id>/chat/', create_chat, name='create_chat'),
    path('messages/<int:chat_id>/', get_messages, name='get_messages'),
    path('ai-chat/', ai_chat, name='ai_chat'),
]