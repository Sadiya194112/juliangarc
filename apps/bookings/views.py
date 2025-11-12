import stripe
import logging
from decimal import Decimal
from datetime import datetime
from django.conf import settings
from django.db.models import Avg
from django.utils import timezone
from  rest_framework import status
from django.http import HttpResponse
# from apps.host.models import Charger
# from apps.Stripe.models import Payment
from apps.bookings.utils import notify_user
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework.exceptions import NotFound
from apps.bookings.models import Booking, Review
from apps.Stripe.utils import setup_stripe_payment
from apps.driver.models import Vehicle, UserVehicle
from django.views.decorators.csrf import csrf_exempt
from stripe._error import SignatureVerificationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.bookings.serializers import BookingCreateSerializer, BookingSerializer, ReviewSerializer
from stripe import CardError, InvalidRequestError, AuthenticationError, APIConnectionError, StripeError
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes


logger = logging.getLogger(__name__)
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
    vehicle_id = request.data.get('vehicle_id')

    if not charger.available or not charger.is_active:
        return Response({'error': 'Charger not available.'}, status=status.HTTP_400_BAD_REQUEST)

    booking_date = serializer.validated_data['booking_date']
    start_time = serializer.validated_data['start_time']
    end_time = serializer.validated_data['end_time']
    
    
    try:
        vehicle = Vehicle.objects.get(id=vehicle_id)
    except Vehicle.DoesNotExist:
        return Response({'error': 'Vehicle not found.'}, status=status.HTTP_404_NOT_FOUND)
    
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
        vehicle=vehicle,
        hourly_rate=charger.price,
        payment_date=booking_date,
        status='pending'
    )
    print("User:", user.get_full_name())  
    print("Host:", station.host.get_full_name()) 
    print("Station:", station.station_name)
    
    data = BookingSerializer(booking).data
    return Response(data, status=status.HTTP_201_CREATED)




@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_booking_details(request, booking_id):
    try:
        # ✅ Logged-in user’s booking
        booking = Booking.objects.get(id=booking_id, user=request.user)

        charging_station = booking.station
        charger = booking.charger
        plug_type = getattr(booking, 'plug', None)
        vehicle = getattr(booking, 'vehicle', None)
        booking_date = booking.booking_date
        start_time = booking.start_time
        end_time = booking.end_time

        # if needed do using check_in_time and check_out_time after finish charging
        if not start_time or not end_time:
            return Response({"error": "Start or End time not available for this booking."},
                            status=status.HTTP_400_BAD_REQUEST)

        # ✅ Combine date + time → datetime objects
        start_dt = datetime.combine(booking_date, start_time)
        end_dt = datetime.combine(booking_date, end_time)

        # If booking crosses midnight, handle properly
        if end_dt < start_dt:
            end_dt += timezone.timedelta(days=1)

        # ✅ Duration calculation
        duration_seconds = (end_dt - start_dt).total_seconds()
        duration_hours = int(duration_seconds // 3600)
        duration_minutes = int((duration_seconds % 3600) // 60)
        duration_seconds = int(duration_seconds % 60)

        # ✅ Price Calculation
        price_per_hour = Decimal(str(charger.price))
        price_per_minute = price_per_hour / Decimal('60')

        subtotal = price_per_hour * Decimal(duration_hours)
        if duration_minutes > 0:
            subtotal += price_per_minute * Decimal(duration_minutes)

        platform_fee = subtotal * Decimal('0.15')
        total_amount = subtotal + platform_fee

        # ✅ Average rating for the charging station
        avg_rating = charging_station.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        avg_rating = round(avg_rating, 1) if avg_rating else "No ratings yet"

        # ✅ Response
        response_data = {
            "vehicle": {
                "model": vehicle.name if vehicle else "N/A",
                "plug_type": plug_type.name if plug_type else "N/A",
                "booking_status": booking.status,
            },
            "charging_station": {
                "station_name": charging_station.station_name,
                "status": charging_station.status,
                "open_time": str(charging_station.opening_time),
                "close_time": str(charging_station.closing_time),
                "rating": avg_rating,
            },
            "booking_details": {
                "booking_id": booking.id,
                "booking_date": str(booking_date),
                "charging_duration": f"{duration_hours:02d}:{duration_minutes:02d}:{duration_seconds:02d}",
                "charging_session_timing": f"{start_time} - {end_time}",
            },
            "pricing": {
                "hourly_rate": str(price_per_hour),
                "subtotal": str(subtotal.quantize(Decimal('0.01'))),
                "platform_fee": str(platform_fee.quantize(Decimal('0.01'))),
                "total_amount": str(total_amount.quantize(Decimal('0.01'))),
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Booking.DoesNotExist:
        return Response({"error": "Booking not found or does not belong to the user."},
                        status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def start_charging_session(request):
    booking_id = request.data.get('booking_id')
    
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
        booking.status = 'in_progress'
        booking.check_in_time = timezone.now()
        booking.save(update_fields=['status','check_in_time'])     
        return Response({'message':'Charging started', 'booking_id': booking.id})
    
    except Booking.DoesNotExist:
        raise NotFound({'error': 'Booking not found or does not belong to the user.'})

    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def charging_activity(request):
    pass


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def stop_charging_session(request):
    booking_id = request.data.get('booking_id')
    
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user, status='in_progress')

        booking.check_out_time = timezone.now()
        booking.status = 'completed'

        # Calculate the duration in seconds and then break it into hours, minutes, and seconds
        duration_seconds = (booking.check_out_time - booking.check_in_time).total_seconds()
        duration_hours = int(duration_seconds // 3600)
        duration_minutes = int((duration_seconds % 3600) // 60)
        duration_seconds = int(duration_seconds % 60) 

        # Pricing logic
        price_per_hour = booking.charger.price 
        price_per_minute = price_per_hour / 60  
        
        # Calculate subtotal based on duration
        subtotal = price_per_hour * Decimal(str(duration_hours))
        
        # If there are remaining minutes, calculate and add the minute price
        if duration_minutes > 0:
            extra_minutes_price = price_per_minute * Decimal(str(duration_minutes))
            subtotal += extra_minutes_price

        # Platform fee (15% of subtotal)
        platform_fee = subtotal * Decimal('0.15')
        total_amount = subtotal + platform_fee

        # Update booking with calculated values
        booking.subtotal = subtotal.quantize(Decimal('0.01'))
        booking.total_amount = total_amount.quantize(Decimal('0.01'))
        booking.save(update_fields=['check_out_time', 'status', 'subtotal', 'total_amount'])

        return Response({
            'message': 'Charging completed',
            'duration_hours': duration_hours,
            'duration_minutes': duration_minutes,
            'duration_seconds': duration_seconds,
            'subtotal': str(booking.subtotal),
            'platform_fee': str(booking.platform_fee),
            'total_amount': str(booking.total_amount)
        })

    except Booking.DoesNotExist:
        return Response({'error': "Booking not found or not in progress."}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)





@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_charging_info(request, booking_id):
    try:
        booking = Booking.objects.select_related(
            'vehicle', 'station__host', 'charger'
        ).get(id=booking_id, user=request.user, status='completed')
        
        # vehicle = booking.vehicle
        
        try:
            user_vehicle = UserVehicle.objects.get(user=request.user)
            vehicle_registration = user_vehicle.registration_number
        except UserVehicle.DoesNotExist:
            vehicle_registration = "N/A"
            
        charging_station = booking.station
        charger = booking.charger
            
        duration_seconds = (booking.check_out_time - booking.check_in_time).total_seconds()
        duration_hours = duration_seconds / 3600  
        
        usage_kwh = booking.charger.power_rating * Decimal(str(duration_hours))


        data = {
            "vehicle_registration": vehicle_registration,
            "station_host": charging_station.host.get_full_name() if charging_station.host else "N/A",
            "station_name": charging_station.station_name,
            "check_in_time": booking.check_in_time.strftime("%Y-%m-%d %H:%M:%S") if booking.check_in_time else "N/A",
            "check_out_time": booking.check_out_time.strftime("%Y-%m-%d %H:%M:%S") if booking.check_out_time else "N/A",
            "usage_kwh": str(round(usage_kwh, 2)) + " kWh",
            "platform_fee": str(booking.platform_fee) + "$"
        }

        return Response(data, status=status.HTTP_200_OK)

    except Booking.DoesNotExist:
        return Response({"error": "Booking not found or not completed."}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def pay_for_booking(request):
    booking_id = request.data.get("booking_id")
    if not booking_id:
        return Response({"error": "booking_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Retrieve the booking object
        booking = Booking.objects.get(id=booking_id, user=request.user, status='completed')

        if booking.is_paid:
            return Response({"message": "This booking is already paid."}, status=status.HTTP_400_BAD_REQUEST)

        # Convert the total amount to cents (Stripe expects the amount in the smallest unit, e.g., cents)
        amount = int(booking.total_amount * 100)
        currency = "usd"  # You can change this to your preferred currency

        # Create a Stripe Checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "product_data": {
                        "name": f"Charging at {booking.station.station_name}",
                        "description": f"EV Charging session #{booking.id}",
                    },
                    "unit_amount": amount,
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=request.user.email,
            metadata={
                "booking_id": booking.id,
                "user_id": request.user.id,
            },
            success_url=f"{settings.FRONTEND_URL}/bookings/payment-success/",
            cancel_url=f"{settings.FRONTEND_URL}/bookings/payment-cancel/",
        )

        # Save the payment intent ID in the booking model
        booking.stripe_payment_intent_id = checkout_session.payment_intent
        booking.save(update_fields=["stripe_payment_intent_id"])

        return Response({
            "checkout_url": checkout_session.url,
            "amount": str(booking.total_amount),
            "currency": currency,
            "message": "Redirect the user to this URL to complete payment."
        }, status=status.HTTP_200_OK)

    except Booking.DoesNotExist:
        return Response({"error": "Booking not found or not completed."}, status=status.HTTP_404_NOT_FOUND)

    # Handle specific Stripe errors
    except CardError as e:
        return Response({"error": f"Card Error: {e.user_message}"}, status=status.HTTP_402_PAYMENT_REQUIRED)

    except InvalidRequestError as e:
        return Response({"error": f"Invalid Request: {e.user_message}"}, status=status.HTTP_400_BAD_REQUEST)

    except AuthenticationError as e:
        return Response({"error": f"Authentication Error: {e.user_message}"}, status=status.HTTP_401_UNAUTHORIZED)

    except APIConnectionError as e:
        return Response({"error": f"API Connection Error: {e.user_message}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except StripeError as e:
        return Response({"error": f"Stripe Error: {e.user_message}"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        return HttpResponse(status=400)
    except SignatureVerificationError:
        logger.error(f"Invalid signature: {str(e)}")
        return HttpResponse(status=400)

    # Handle the payment success event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        booking_id = session['metadata']['booking_id']

        try:
            booking = Booking.objects.get(id=booking_id)

            # Update the booking as paid
            booking.is_paid = True
            booking.payment_date = timezone.now()
            booking.save(update_fields=["is_paid", "payment_date"])

            logger.info(f"Booking #{booking.id} payment successful.")

            return HttpResponse(status=200)

        except Booking.DoesNotExist:
            logger.error(f"Booking not found for ID: {booking_id}")
            return HttpResponse(status=404)

    else:
        logger.error(f"Unhandled event type: {event['type']}")
        return HttpResponse(status=200)  
    
    
    
    
    

    
    


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

