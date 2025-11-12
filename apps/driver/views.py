import requests
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from apps.driver.models import Vehicle, PlugType, UserVehicle
from apps.driver.utils import calculate_distance
from rest_framework.permissions import IsAuthenticated
from apps.host.models import ChargingStation, Charger, ChargerType
from apps.host.serializers import ChargingStationSerializer, ChargerSerializer, ChargerTypeSerializer
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
    
    serializer = VehicleSerializer(queryset, many=True, context={'request': request})
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
        is_default = request.data.get("is_default", False)
        
        if is_default:
            UserVehicle.objects.filter(user=request.user).update(is_default=False)
        
        user_vehicle = serializer.save(user=request.user)

        if is_default:
            user_vehicle.is_default = True
            user_vehicle.save()
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

    station_id = request.query_params.get('station_id', None)
    lat = request.query_params.get('latitude', None)
    lon = request.query_params.get('longitude', None)
    radius_km = float(request.query_params.get('radius', 50))

    # lat/lon must be provided for both nearby and station-specific mode
    if lat is None or lon is None:
        return Response({"error": "latitude and longitude are required"}, status=400)

    lat = float(lat)
    lon = float(lon)

    # Fetch all stations first
    all_stations = list(ChargingStation.objects.all())
    stations_with_info = []

    # Calculate distances in chunks
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

    # Sort by distance
    stations_with_info.sort(key=lambda x: x["distance"])

    # ✅ If station_id is passed, return only that station (if inside radius list)
    if station_id:
        matched = next((s for s in stations_with_info if str(s["station"].id) == station_id), None)

        if not matched:
            return Response({"error": "Station not found within the specified radius"}, status=404)

        station = matched["station"]

        # Serialize station
        serializer = ChargingStationSerializer(station)
        data = serializer.data
        data["distance_km"] = matched["distance"]
        data["time_to_reach_min"] = matched["time_to_reach"]

        # ✅ Include charger details
        chargers = Charger.objects.filter(station=station).select_related('charger_type').prefetch_related('plug_types', 'connector_types')

        data["chargers"] = [{
            "id": c.id,
            "name": c.name,
            "charger_type": c.charger_type.name if c.charger_type else None,
            "mode": c.mode,
            "price": c.price,
            "available": c.available,
            # "extended_time_unit": c.extended_time_unit,
            # "extended_price_per_unit": c.extended_price_per_unit,
            "plug_types": [{"id": p.id, "name": p.name} for p in c.plug_types.all()],
            "connector_types": [{"id": c2.id, "name": c2.name} for c2 in c.connector_types.all()],
        } for c in chargers]

        return Response(data, status=200)

    # ✅ Otherwise return the full nearby list
    serializer = ChargingStationSerializer([i["station"] for i in stations_with_info], many=True)

    response_data = []
    for data_item, extra in zip(serializer.data, stations_with_info):
        data_item["distance_km"] = extra["distance"]
        data_item["time_to_reach_min"] = extra["time_to_reach"]
        response_data.append(data_item)

    return Response(response_data, status=200)





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
def get_charger_types(request):
    """
    Get all Charger Types.
    """
    charger_types = ChargerType.objects.all()  
    serializer = ChargerTypeSerializer(charger_types, many=True)  
    return Response(serializer.data, status=status.HTTP_200_OK)