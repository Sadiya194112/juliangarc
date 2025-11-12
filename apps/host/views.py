import stripe
import logging
from django.db.models import Q
from rest_framework import status
from apps.driver.models import PlugType
from apps.bookings.models import Booking
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from apps.subscriptions.models import Subscription
from rest_framework.permissions import IsAuthenticated
from apps.host.utlis import create_booking_notification
from rest_framework.parsers import MultiPartParser, FormParser
from apps.host.models import ChargingStation, Charger, ConnectorType
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from apps.bookings.serializers import BookingSerializer, BookingHostViewSerializer, BookingCompletedSerializer
from apps.host.serializers import ChargerCreateSerializer, ChargerSerializer, ChargingStationSerializer, PlugTypeSerializer, ConnectorTypeSerializer

 
logger = logging.getLogger(__name__)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def plug_and_connector_types(request):
    plug_types = PlugType.objects.all()
    connector_types = ConnectorType.objects.all()

    plug_serializer = PlugTypeSerializer(plug_types, many=True)
    connector_serializer = ConnectorTypeSerializer(connector_types, many=True)

    return Response({
        "plug_types": plug_serializer.data,
        "connector_types": connector_serializer.data
    }, status=status.HTTP_200_OK)




@swagger_auto_schema(method='post', request_body=ChargerCreateSerializer, tags=['Booking'])
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
# @parser_classes([MultiPartParser, FormParser])
def add_charger(request):
    user = request.user

    if user.role != 'host':
        return Response({'error': 'Only hosts can add chargers.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = ChargerCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        charger = serializer.save()

        is_default = request.data.get("is_default", False)
        
        if is_default:
            Charger.objects.filter(station__host=user).update(is_default=False)
            charger.is_default = True
            charger.save()
        return Response({
            "message": "Charger added successfully.",
            "charger_id": charger.id,
            "station": charger.station.station_name,
            "extended_price_example": f"{charger.extended_price_per_unit} per {charger.extended_time_unit} unit"
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@swagger_auto_schema(method='get', request_body=ChargerSerializer, tags=['Charger'])
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def chargers_list(request):
    chargers = Charger.objects.select_related('charger_type', 'station').prefetch_related('plug_types', 'connector_types')
    serializer = ChargerSerializer(chargers, many=True)
    return Response(serializer.data, status=200)



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def charging_station_list(request):
    """
    List all charging stations with optional search support.
    """
    queryset = ChargingStation.objects.all()

    # ---- SEARCH ----
    search_query = request.GET.get('search')
    if search_query:
        queryset = queryset.filter(
            Q(station_name__icontains=search_query) |
            Q(location_area__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(host__full_name__icontains=search_query)
        )

    serializer = ChargingStationSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def host_booking_list(request):
    user = request.user
    

    # ✅ 1. শুধুমাত্র host-কে অনুমতি দাও
    if user.role != 'host':
        return Response({'error': 'Only hosts can see booking lists.'}, status=status.HTTP_403_FORBIDDEN)

    # ✅ 2. Query parameter থেকে status নাও
    status_filter = request.GET.get('status', 'all').strip().lower()
    valid_statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']

    # ✅ 3. Host-এর station গুলো বের করো
    stations = ChargingStation.objects.filter(host=user)

    # ✅ 4. Base queryset
    bookings = (
        Booking.objects.filter(station__in=stations)
        .select_related('station', 'user')
        .order_by('-created_at')
    )

    # ✅ 5. যদি filter apply করতে হয়
    if status_filter != 'all':
        if status_filter not in valid_statuses:
            return Response({'error': 'Invalid status filter.'}, status=status.HTTP_400_BAD_REQUEST)
        # ✅ Case-insensitive exact match
        bookings = bookings.filter(status__iexact=status_filter)

    # # ✅ 6. Filter করা ফলাফল debug করতে পারো
    # print("Applied Filter:", status_filter, "| Found:", bookings.count())

    # ✅ 7. Serializer নির্বাচন
    if status_filter == 'completed':
        serializer = BookingCompletedSerializer(bookings, many=True)
    else:
        serializer = BookingHostViewSerializer(bookings, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)




@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def change_status(request):
    """
    PATCH → change charger status
    """
    charger_id = request.data.get('charger_id')
    new_status = request.data.get('status')

    try:
        charger = Charger.objects.get(id=charger_id, station__host=request.user)
    except Charger.DoesNotExist:
        return Response({'error': 'Charger not found'}, status=status.HTTP_404_NOT_FOUND)

    charger.status = new_status
    charger.save()

    serializer = ChargerSerializer(charger)
    return Response(serializer.data, status=status.HTTP_200_OK)



# ✅ Host: Booking Accept / Reject করা
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def booking_status_update(request, pk):
    user = request.user
    if user.role != 'host':
        return Response({'error': 'Only hosts can update booking status.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        booking = Booking.objects.get(pk=pk, charger__station__host=user)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found or not your station.'}, status=status.HTTP_404_NOT_FOUND)

    status_value = request.data.get('status')
    if status_value not in ['accept', 'reject']:
        return Response({'error': 'Invalid status value.'}, status=status.HTTP_400_BAD_REQUEST)

    if status_value == 'accept':
        booking.status = 'confirmed'
    elif status_value == 'reject':
        booking.status = 'cancelled'
    booking.save()

    # 🔔 Notification পাঠানো হচ্ছে
    create_booking_notification(booking, status_value)

    return Response({'success': f'Booking {status_value} successfully.'}, status=status.HTTP_200_OK)



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def upcoming_reservations(request):
    """
    Get upcoming reservations (pending or confirmed) for the authenticated user.
    Returns user/driver name, vehicle name, status, start time, end time, and booking date.
    """
    user = request.user

    bookings = Booking.objects.filter(
        station__host=user,
        status__in=['pending', 'confirmed']  
    ).select_related('user', 'vehicle').order_by('booking_date', 'start_time')

    print(f"Bookings found for user {user.id}: {bookings.count()}") 

    if not bookings.exists():
        return Response({"message": "No upcoming reservations."}, status=status.HTTP_200_OK)

    reservation_data = []

    for booking in bookings:
        reservation_data.append({
            "booking_id": booking.id,                                           
            "user_name": booking.user.full_name,
            "vehicle_name": booking.vehicle.name,
            "status": booking.status,
            "start_time": booking.start_time.strftime("%I:%M %p"),                                          
            "end_time": booking.end_time.strftime("%I:%M %p"),
            "booking_date": booking.booking_date.strftime("%Y-%m-%d"),
        })

    return Response({"upcoming_reservations": reservation_data}, status=status.HTTP_200_OK)




@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def host_dashboard(request):
    user = request.user

    if user.role != 'host':
        return Response({'error': 'Only hosts can access this dashboard.'}, status=status.HTTP_403_FORBIDDEN)

    # Fetch Stripe Account Status
    stripe_account_status = None
    print("Stripe Account ID:", user.stripe_account_id)  # Log the account ID
    if user.stripe_account_id:
        try:
            account = stripe.Account.retrieve(user.stripe_account_id)
            # print("Full Account Info:", account)

            stripe_account_status = account['charges_enabled']
            print("Stripe Account Status:", stripe_account_status)  # Log the account status
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving account: {e}")
            stripe_account_status = "Error retrieving account status"
        except Exception as e:
            logger.error(f"Unexpected error during account retrieval: {str(e)}")
            stripe_account_status = "Error retrieving account status"
    else:
        logger.error("No Stripe account ID found for user.")
        stripe_account_status = "No Stripe account linked"

    # Get the active subscription plan for the host
    active_subscription = Subscription.objects.filter(user=user, status='active').first()
    if active_subscription:
        current_plan = active_subscription.plan.name
        next_billing_date = active_subscription.end_date
    else:
        current_plan = "No active plan"
        next_billing_date = None

    # Count active and inactive chargers for the host
    station = ChargingStation.objects.filter(host=user).first()
    if station:
        active_chargers_count = Charger.objects.filter(station=station, is_active=True).count()
        inactive_chargers_count = Charger.objects.filter(station=station, is_active=False).count()
    else:
        active_chargers_count = 0
        inactive_chargers_count = 0

    # Calculate average rating and review count for the host's charging station
    if station:
        total_reviews = station.reviews.count()
        average_rating = station.average_rating
    else:
        total_reviews = 0
        average_rating = 0

    # Return the host's dashboard information
    return Response({
        "payment_setup": {
            "stripe_status": (
                "Verified" if stripe_account_status is True 
                else "Not Verified" if stripe_account_status is False 
                else "No Stripe account linked"
            )
        },
        "subscription_plan": {
            "current_plan": current_plan,
            "next_billing_date": next_billing_date.strftime('%b %d, %Y') if next_billing_date else None,
        },
        "chargers": {
            "active_chargers": active_chargers_count,
            "inactive_chargers": inactive_chargers_count
        },
        "ratings_and_reviews": {
            "average_rating": average_rating,
            "total_reviews": total_reviews
        }
    }, status=status.HTTP_200_OK)




# @api_view(['GET'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def user_booking_list(request):
#     user = request.user
#     if user.role != 'host':
#         return Response({'error': 'Only host can view bookings.'}, status=status.HTTP_403_FORBIDDEN)

#     status_filter = request.GET.get('status', 'all').lower()  # default = all

#     bookings = Booking.objects.filter(station__host=user).order_by('-created_at')

#     # filter প্রয়োগ
#     if status_filter != 'all':
#         valid_statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']
#         if status_filter not in valid_statuses:
#             return Response({'error': 'Invalid status filter.'}, status=status.HTTP_400_BAD_REQUEST)
#         bookings = bookings.filter(status=status_filter)

#     serializer = BookingListSerializer(bookings, many=True)
#     return Response(serializer.data, status=status.HTTP_200_OK)



# @api_view(['GET', 'POST'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def charging_station_list_create(request):
#     """
#     GET  → all stations created by logged-in host
#     POST → create new charging station
#     """
#     if request.method == 'GET':
#         stations = ChargingStation.objects.filter(host=request.user)
#         serializer = ChargingStationSerializer(stations, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     elif request.method == 'POST':
#         serializer = ChargingStationSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save(host=request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# @api_view(['GET', 'PATCH', 'DELETE'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def charging_station_detail(request, pk):
#     """
#     GET → single station details
#     PATCH → update station
#     DELETE → delete station
#     """
#     try:
#         station = ChargingStation.objects.get(pk=pk)
#     except ChargingStation.DoesNotExist:
#         return Response({'error': 'Station not found'}, status=status.HTTP_404_NOT_FOUND)

#     if request.method == 'GET':
#         serializer = ChargingStationSerializer(station)
#         return Response(serializer.data)

#     elif request.method == 'PATCH':
#         serializer = ChargingStationSerializer(station, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save(host=request.user)
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     elif request.method == 'DELETE':
#         station.delete()
#         return Response({'message': 'Station deleted'}, status=status.HTTP_204_NO_CONTENT)
    



# @api_view(['GET'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def get_chargers(request):
#     """
#     GET → all chargers created by logged-in host
#     """
#     stations = ChargerDetail.objects.filter(station__host=request.user)
#     serializer = ChargerDetailSerializer(stations, many=True)
#     return Response(serializer.data, status=status.HTTP_200_OK)



