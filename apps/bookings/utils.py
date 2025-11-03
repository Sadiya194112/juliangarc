from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def notify_user(user_id, payload):
    """
    Send realtime notification to a specific user via Channels
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",  # same group name as consumer
        {
            "type": "booking.notification",
            "payload": payload
        }
    )