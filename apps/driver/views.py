import requests
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from apps.driver.models import Vehicle, PlugType, UserVehicle
from apps.driver.utils import calculate_distance
from rest_framework.permissions import IsAuthenticated
from apps.host.models import ChargingStation, Charger
from apps.host.serializers import ChargingStationSerializer, ChargerSerializer
from apps.driver.serializers import VehicleSerializer, UserVehicleSerializer, PlugTypeSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.db.models import Q


# @api_view(['GET', 'POST'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def driver_vehicle_list_create(request):
#     """
#     GET  → logged-in driver's vehicles list
#     POST → create new vehicle for driver
#     """
#     if request.method == 'GET':
#         vehicles = DriverVehicle.objects.filter(user=request.user)
#         serializer = DriverVehicleSerializer(vehicles, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     elif request.method == 'POST':
#         serializer = DriverVehicleSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



# @api_view(['GET', 'PUT', 'DELETE'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def driver_vehicle_detail(request, pk):
#     """
#     GET → single vehicle details
#     PUT → update vehicle
#     DELETE → remove vehicle
#     """
#     try:
#         vehicle = DriverVehicle.objects.get(pk=pk, user=request.user)
#     except DriverVehicle.DoesNotExist:
#         return Response({'error': 'Vehicle not found'}, status=status.HTTP_404_NOT_FOUND)

#     if request.method == 'GET':
#         serializer = DriverVehicleSerializer(vehicle)
#         return Response(serializer.data)

#     elif request.method == 'PUT':
#         serializer = DriverVehicleSerializer(vehicle, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     elif request.method == 'DELETE':
#         vehicle.delete()
#         return Response({'message': 'Vehicle deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def vehicle_list(request):
    """
    List all Vehicles with optional search by 'name' or 'vehicle_type'.
    """
    search_query = request.query_params.get('search')
    queryset = Vehicle.objects.all()
    
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) | Q(vehicle_type__icontains=search_query)
        )
    
    serializer = VehicleSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def plug_type_list(request):
    """
    List all Plug Types.
    """
    queryset = PlugType.objects.all()
    serializer = PlugTypeSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_user_vehicle(request):
    serializer = UserVehicleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response({
            "message": "Vehicle added successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- List all vehicles for the logged-in user ---
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_vehicle_list(request):
    """
    List all vehicles of the logged-in user.
    """
    queryset = UserVehicle.objects.filter(user=request.user)
    serializer = UserVehicleSerializer(queryset, many=True)
    return Response(serializer.data)


# --- Retrieve Vehicle ---
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_vehicle_detail(request, pk):
    try:
        vehicle = UserVehicle.objects.get(pk=pk, user=request.user)
    except UserVehicle.DoesNotExist:
        return Response({'detail': 'Not found or forbidden.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserVehicleSerializer(vehicle)
    return Response(serializer.data)


# --- Update Vehicle ---
@api_view(['PUT', 'PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_vehicle_update(request, pk):
    try:
        vehicle = UserVehicle.objects.get(pk=pk, user=request.user)
    except UserVehicle.DoesNotExist:
        return Response({'detail': 'Not found or forbidden.'}, status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = UserVehicleSerializer(vehicle, data=request.data, partial=partial)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- Delete Vehicle ---
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def user_vehicle_delete(request, pk):
    try:
        vehicle = UserVehicle.objects.get(pk=pk, user=request.user)
    except UserVehicle.DoesNotExist:
        return Response({'detail': 'Not found or forbidden.'}, status=status.HTTP_404_NOT_FOUND)

    vehicle.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)



def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def nearby_stations(request):
    lat = float(request.query_params.get('latitude', 0))
    lon = float(request.query_params.get('longitude', 0))
    radius_km = float(request.query_params.get('radius', 50))

    # Fetch all available stations
    all_stations = list(ChargingStation.objects.filter())
    stations_with_info = []

    # Break into chunks to avoid API limit
    for station_chunk in chunks(all_stations, 25):
        destinations = [f"{s.latitude},{s.longitude}" for s in station_chunk]
        origins = f"{lat},{lon}"

        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": origins,
            "destinations": "|".join(destinations),
            "key": settings.GOOGLE_MAPS_API_KEY,
            "units": "metric"
        }

        response = requests.get(url, params=params)
        data = response.json()

        if "rows" in data and len(data["rows"]) > 0 and "elements" in data["rows"][0]:
            for i, element in enumerate(data["rows"][0]["elements"]):
                if element.get("status") == "OK":
                    distance_km = element["distance"]["value"] / 1000
                    duration_min = element["duration"]["value"] / 60

                    if distance_km <= radius_km:
                        stations_with_info.append({
                            "station": station_chunk[i],
                            "distance": round(distance_km, 2),
                            "time_to_reach": round(duration_min, 1)
                        })
        else:
            print("Google Distance Matrix API returned empty rows or error:", data)

    # Sort by distance
    stations_with_info.sort(key=lambda x: x["distance"])

    # Serialize station + details
    serializer = ChargingStationSerializer(
        [item["station"] for item in stations_with_info],
        many=True
    )

    # Merge extra fields (distance, time)
    response_data = []
    for data_item, extra in zip(serializer.data, stations_with_info):
        data_item["distance_km"] = extra["distance"]
        data_item["time_to_reach_min"] = extra["time_to_reach"]
        response_data.append(data_item)

    return Response(response_data, status=status.HTTP_200_OK)




@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def chargers_list(request):
    chargers = Charger.objects.select_related('charger_type', 'station').prefetch_related('plug_types', 'connector_types')
    serializer = ChargerSerializer(chargers, many=True)
    return Response(serializer.data, status=200)

