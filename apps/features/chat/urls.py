from django.urls import path
from apps.features.chat.views import my_chats, create_chat, get_messages, ai_chat, driver_host_chat_list, driver_chat_list



urlpatterns = [
    path('my-chats/', my_chats, name='my_chats'),
    path('create/<int:host_id>/chat/', create_chat, name='create_chat'),
    path('messages/<int:chat_id>/', get_messages, name='get_messages'),
    path('all-station-chats/', driver_host_chat_list, name='all-station-chats'),
    path('users-chat-with-station/', driver_chat_list, name='users-chat-with-station'),
    path('ai-chat/', ai_chat, name='ai_chat'),
]