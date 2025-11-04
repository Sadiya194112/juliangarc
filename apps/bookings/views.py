import stripe
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from  rest_framework import status
from apps.host.models import Charger
from apps.Stripe.models import Payment
from apps.bookings.utils import notify_user
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from apps.bookings.models import Booking, Review
from apps.Stripe.utils import setup_stripe_payment
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.bookings.serializers import BookingCreateSerializer, BookingSerializer, ReviewSerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes


stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_booking(request):
    user = request.user
    if getattr(user, 'role', 'user') != 'user':
        return Response({'error': 'Only users can create bookings.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = BookingCreateSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    charger = serializer.validated_data['charger']
    station = serializer.validated_data['station']  # ✅ instance directly
    plug = serializer.validated_data['plug']

    if not charger.available or not charger.is_active:
        return Response({'error': 'Charger not available.'}, status=status.HTTP_400_BAD_REQUEST)

    booking_date = serializer.validated_data['booking_date']
    start_time = serializer.validated_data['start_time']
    end_time = serializer.validated_data['end_time']

    # Overlap check
    overlap_qs = Booking.objects.filter(
        charger=charger,
        booking_date=booking_date,
        start_time__lt=end_time,
        end_time__gt=start_time,
        status__in=['pending', 'confirmed', 'in_progress']
    )
    if overlap_qs.exists():
        notify_user(user.id, {
            'type': 'booking_conflict',
            'message': f"Charger '{charger.name}' is not available from {start_time} to {end_time}."
        })
        return Response({'error': "This charger isn't available in the selected time range. Realtime notification sent."},
                        status=status.HTTP_400_BAD_REQUEST)

    # ✅ Station এবং charger instance হিসেবে save করা
    booking = serializer.save(
        user=user,
        station=station,
        charger=charger,
        plug=plug,
        hourly_rate=charger.price,
        payment_date=booking_date,
        status='pending'
    )

    data = BookingSerializer(booking).data
    return Response(data, status=status.HTTP_201_CREATED)







@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def start_charging_session(request):
    booking_id = request.data.get('booking_id')
    booking = Booking.objects.get(id=booking_id, user=request.user)

    booking.status = 'in_progress'
    booking.check_in_time = timezone.now()
    booking.save(update_fields=['status','check_in_time'])
    return Response({'message':'Charging started', 'booking_id': booking.id})



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stop_charging_session(request):
    booking_id = request.data.get('booking_id')
    booking = Booking.objects.get(id=booking_id, user=request.user, status='in_progress')

    booking.check_out_time = timezone.now()
    booking.status = 'completed'

    duration_seconds = (booking.check_out_time - booking.check_in_time).total_seconds()
    duration_hours = duration_seconds / 3600  


    price_per_hour = booking.charger.price

    # subtotal = price_per_hour * duration
    subtotal = price_per_hour * Decimal(str(duration_hours))

    # platform
    platform_fee = subtotal * Decimal('0.15')  # 15% platform fee
    total_amount = subtotal + platform_fee

    booking.subtotal = subtotal.quantize(Decimal('0.01'))
    booking.total_amount = total_amount.quantize(Decimal('0.01'))
    booking.save(update_fields=['check_out_time','status','subtotal','total_amount'])

    return Response({
        'message': 'Charging completed',
        'duration_hours': round(duration_hours,2),
        'subtotal': str(booking.subtotal),
        'total_amount': str(booking.total_amount)
    })





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