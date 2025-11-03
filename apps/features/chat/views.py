from rest_framework import status
from apps.accounts.models import User
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.features.ai.chatbot import EVChargingChatbot
from apps.features.chat.models import ChatRoom, Message
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.features.chat.serializers import ChatRoomSerializer, MessageSerializer
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.db.models import Q


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def my_chats(request):
    user = request.user
    search_query = request.query_params.get('search', '')

    # Filter chats where user is driver or host
    chats = ChatRoom.objects.filter(driver=user) | ChatRoom.objects.filter(host=user)

    # If search query exists, filter by title or participant's name
    if search_query:
        chats = chats.filter(
            Q(host__host_profile__station_name__icontains=search_query) |
            Q(driver__full_name__icontains=search_query) |
            Q(host__full_name__icontains=search_query)
        )

    # Remove duplicates if any due to OR filtering
    chats = chats.distinct()

    serializer = ChatRoomSerializer(chats, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_chat(request, host_id):
    driver = request.user
    try:
        host = User.objects.get(id=host_id)
    except User.DoesNotExist:
        return Response({"error": "Host not found"}, status=status.HTTP_404_NOT_FOUND)

    chat, created = ChatRoom.objects.get_or_create(driver=driver, host=host)
    serializer = ChatRoomSerializer(chat)
    return Response(serializer.data, status=status.HTTP_201_CREATED)



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_messages(request, chat_id):
    try:
        chat = ChatRoom.objects.get(id=chat_id)
    except ChatRoom.DoesNotExist:
        return Response({"error": "Chat not found."}, status=status.HTTP_404_NOT_FOUND)

    messages = chat.messages.all().order_by('timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def driver_host_chat_list(request):
    user = request.user

    # Driver joto host er sathe chat koreche (AI chat chara)
    chats = (
        ChatRoom.objects
        .filter(driver=user, is_ai_chat=False)
        .select_related('host')
        .order_by('host_id')  # group-ish
    )

    result = []

    for chat in chats:
        last_msg = chat.messages.order_by('-timestamp').first()
        host = chat.host
        
        result.append({
            "chat_room_id": chat.id,
            "host": {
                "id": host.id,
                "name": host.full_name,
                "email": host.email,
                "profile_image": host.profile_image.url if hasattr(host, "profile_image") and host.profile_image else None,
            },
            "last_message": last_msg.text if last_msg else None,
            "last_message_time": last_msg.timestamp if last_msg else None
        })

    return Response({"hosts": result}, status=status.HTTP_200_OK)




@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def ai_chat(request):
    """
    Driver ↔ AI chat endpoint
    """
    user = request.user
    query = request.data.get('text', '').strip()
    latitude = float(request.query_params.get('latitude', 0))
    longitude = float(request.query_params.get('longitude', 0))
    
    if not query:
        return Response({"error": "Text Message is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    chat, created = ChatRoom.objects.get_or_create(driver=user, is_ai_chat=True)
    
    user_message = Message.objects.create(
        chat=chat,
        sender=user,
        text=query,
        is_from_ai=False
    )
    
    chatbot = EVChargingChatbot()
    

    
    history = list(chat.messages.values('is_from_ai', 'text').order_by('timestamp'))
    formatted_history = [
        {'role': 'bot' if h['is_from_ai'] else "user", "content": h['text']} for h in history
    ]
    
    ai_reply = chatbot.get_response(
        query,
        formatted_history,
        latitude,
        longitude
    )
        
    ai_message = Message.objects.create(
        chat=chat,
        text=ai_reply,
        is_from_ai=True
    )
    
    serializer = MessageSerializer([user_message, ai_message], many=True)
    return Response(serializer.data, status=status.HTTP_201_CREATED)





