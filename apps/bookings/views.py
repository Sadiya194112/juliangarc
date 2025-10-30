import stripe
from django.conf import settings
from  rest_framework import status
from apps.Stripe.models import Payment
from apps.host.models import Charger
from rest_framework.response import Response
from apps.bookings.models import Booking, Review
from apps.Stripe.utils import setup_stripe_payment
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from apps.bookings.serializers import BookingCreateSerializer, BookingSerializer, ReviewSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema


stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_booking(request):
    if request.user.role != 'driver':
        return Response({'error': 'Only drivers can create bookings.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = BookingCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        charger = Charger.objects.get(
            id=serializer.validated_data['charger'].id,
            available=True
        )
    except Charger.DoesNotExist:
        return Response({'error': 'Charger not found or unavailable.'}, status=status.HTTP_404_NOT_FOUND)

    start = serializer.validated_data['start_datetime']
    end = serializer.validated_data['end_datetime']

    if Booking.objects.filter(
        charger=charger,
        status__in=['confirmed', 'in_progress'],
        start_datetime__lt=end,
        end_datetime__gt=start
    ).exists():
        return Response({'error': 'Charger not available in this time slot.'}, status=status.HTTP_400_BAD_REQUEST)

    booking = serializer.save(
        driver=request.user,
        host=charger.station.host,
        hourly_rate=charger.price_per_hour,
    )

    try:
        client_secret = setup_stripe_payment(booking, request.user)
        booking.stripe_payment_intent_id = client_secret
        booking.save()
    except Exception as e:
        booking.delete()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    data = BookingSerializer(booking).data
    data['client_secret'] = client_secret
    return Response(data, status=status.HTTP_201_CREATED)



# @api_view(['POST'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def submit_review(request):
#     """
#     Driver gives a review for a completed booking.
#     """
#     serializer = ReviewSerializer(data=request.data, context={'request': request})
#     if serializer.is_valid():
#         serializer.save()
#         return Response({'message': 'Review submitted successfully!'}, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', request_body=ReviewSerializer, tags=['Booking'])
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
# @parser_classes([MultiPartParser, FormParser])
def submit_review(request):
    """
    Submit a review with multiple images for a charging station.
    """
    serializer = ReviewSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Review submitted successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
