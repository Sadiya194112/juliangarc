import stripe
from decimal import Decimal
from datetime import datetime
from django.conf import settings
from django.db.models import Avg
from django.utils import timezone
from  rest_framework import status
from apps.host.models import Charger
from apps.Stripe.models import Payment
from apps.bookings.utils import notify_user
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework.exceptions import NotFound
from apps.bookings.models import Booking, Review
from apps.Stripe.utils import setup_stripe_payment
from apps.driver.models import Vehicle, UserVehicle
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.bookings.serializers import BookingCreateSerializer, BookingSerializer, ReviewSerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def booking_list(request):
    """Get the list of bookings for the authenticated user."""
    user = request.user  
    bookings = Booking.objects.filter(user=user).order_by('-created_at')  
    
    serializer = BookingSerializer(bookings, many=True)

    return Response(serializer.data)


@api_view(['GET'])
def payment_success(request):
    return Response({"message": "Payment successful!"}, status=200)



@api_view(['GET'])
def payment_cancel(request):
    return Response({"message": "Payment canceled!"}, status=200)



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_charging_history(request):
    try:
        bookings = (
            Booking.objects.select_related('station', 'charger', 'vehicle', 'plug')
            .filter(user=request.user, status='completed')
            .order_by('-booking_date')
        )
        if not bookings.exists():
            return Response({"message": "No charging history found."}, status=status.HTTP_200_OK)
        
        
        history_data = []
        for booking in bookings:
            duration_hours = 0
            usage_kwh = 0
            
            if booking.check_in_time and booking.check_out_time:
                duration_seconds = (booking.check_out_time - booking.check_in_time).total_seconds()
                duration_hours = duration_seconds / 3600
                usage_kwh = booking.charger.power_rating * Decimal(str(duration_hours))
            
            vehicle_name = booking.vehicle.name if booking.vehicle else "N/A"
            plug_type_name = booking.plug.name if booking.plug else "N/A" 
            
            history_data.append({
                "booking_id": booking.id,
                "vehicle_name": vehicle_name,
                "plug_type": plug_type_name,
                "station_name": booking.station.station_name,
                "booking_date": booking.booking_date.strftime("%Y-%m-%d"),
                "usage_kwh": f"{round(usage_kwh, 2)} kWh",
                "price": f"{booking.total_amount} $"
            })
        
        return Response({"history": history_data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def charging_history_detail(request, booking_id):
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
        
        #charger details
        charging_fee = booking.subtotal
        platform_fee = booking.platform_fee
        total_fee = booking.total_amount
        
        # ✅ Station rating
        avg_rating = charging_station.reviews.aggregate(avg=Avg('rating'))['avg']
        avg_rating = round(avg_rating, 1) if avg_rating else 0

        data = {
            "vehicle_information": {
                "license_plate": vehicle_registration,
                "vehicle_name": booking.vehicle.name
            },
            "station_information": {
                "operator": charging_station.host.get_full_name() if charging_station.host else "N/A",
                "station_name": charging_station.station_name,
                "rating": avg_rating,
                "open_status": "Open" if charging_station.is_currently_open else "Closed",
                "opening_time": charging_station.opening_time.strftime("%H:%M"),
                "closing_time": charging_station.closing_time.strftime("%H:%M")
            },
            "charge_details": {
                "charging_fee": f"{charging_fee} USD",
                "charging_rate": f"{charger.power_rating} kW/h",
                "platform_fee": f"{platform_fee} USD",
                "total_fee": f"{total_fee} USD"
            },
            "timing": {
                "start_charging": booking.check_in_time.strftime("%Y-%m-%d %H:%M") if booking.check_in_time else "N/A",
                "finish_charging": booking.check_out_time.strftime("%Y-%m-%d %H:%M") if booking.check_out_time else "N/A"
            }
        }

        return Response(data, status=status.HTTP_200_OK)

    except Booking.DoesNotExist:
        return Response({"error": "Booking not found or not completed."}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)