# import stripe
# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from apps.host.models import ChargingStation, ChargerDetail
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from apps.host.serializers import ChargingStationSerializer, ChargerDetailSerializer
# from rest_framework.decorators import api_view, authentication_classes, permission_classes
# from django.db.models import Q


# @api_view(['GET'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def charging_station_list(request):
#     """
#     List all charging stations with optional search support.
#     """
#     queryset = ChargingStation.objects.all()

#     # ---- SEARCH ----
#     search_query = request.GET.get('search')
#     if search_query:
#         queryset = queryset.filter(
#             Q(station_name__icontains=search_query) |
#             Q(location_area__icontains=search_query) |
#             Q(address__icontains=search_query) |
#             Q(host__full_name__icontains=search_query)
#         )

#     serializer = ChargingStationSerializer(queryset, many=True, context={'request': request})
#     return Response(serializer.data)


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



# @api_view(['PATCH'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def change_status(request):
#     """
#     PATCH → change charger status
#     """
#     charger_id = request.data.get('charger_id')
#     new_status = request.data.get('status')

#     try:
#         charger = ChargerDetail.objects.get(id=charger_id, station__host=request.user)
#     except ChargerDetail.DoesNotExist:
#         return Response({'error': 'Charger not found'}, status=status.HTTP_404_NOT_FOUND)

#     charger.status = new_status
#     charger.save()

#     serializer = ChargerDetailSerializer(charger)
#     return Response(serializer.data, status=status.HTTP_200_OK)