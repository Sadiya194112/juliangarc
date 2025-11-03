from django.db.models import Q
from rest_framework import status
from apps.bookings.models import Booking
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from apps.host.models import ChargingStation, Charger
from rest_framework.permissions import IsAuthenticated
from apps.bookings.serializers import BookingSerializer
from apps.host.serializers import ChargerCreateSerializer, ChargerSerializer, ChargingStationSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes



@swagger_auto_schema(method='post', request_body=ChargerCreateSerializer, tags=['Booking'])
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
# @parser_classes([MultiPartParser, FormParser])
def add_charger(request):
    serializer = ChargerCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        charger = serializer.save()
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
    
    if user.role != 'host':
        return Response({'error': 'Only hosts can see booking lists.'}, status=status.HTTP_403_FORBIDDEN)
    
    # ✅ স্টেশনগুলো পাই
    stations = ChargingStation.objects.filter(host=user)
    
    # ✅ স্টেশনগুলোর সব বুকিং পাই
    bookings = Booking.objects.filter(station__in=stations).order_by('-created_at')
    
    serializer = BookingSerializer(bookings, many=True)
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



