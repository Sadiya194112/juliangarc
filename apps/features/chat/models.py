from django.db import models
from apps.accounts.models import User


class ChatRoom(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='driver_chats')
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='host_chats', null=True, blank=True)
    is_ai_chat = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('driver', 'host')

    def __str__(self):
        if self.is_ai_chat:
            return f"AI Chat with {self.driver.full_name}"
        return f"{self.driver.full_name} and {self.host.full_name}"


class Message(models.Model):
    chat = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', null=True, blank=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)

    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    location = models.JSONField(blank=True, null=True)  # {'lat': 23.45, 'lon': 90.34}
    is_from_ai = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):
        """
        Automatically determine the receiver before saving.
        """
        if self.sender and not self.receiver:
            if self.chat.is_ai_chat:
                # In AI chats, sender is always the human; receiver is 'AI'
                self.receiver = None
            else:
                if self.sender == self.chat.driver:
                    self.receiver = self.chat.host
                else:
                    self.receiver = self.chat.driver
        super().save(*args, **kwargs)

    def __str__(self):
        sender_name = self.sender.full_name if self.sender else "Unknown"
        receiver_name = self.receiver.full_name if self.receiver else "AI"
        return f"{sender_name} → {receiver_name} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"