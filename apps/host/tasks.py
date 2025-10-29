# import googlemaps
# from celery import shared_task
# from django.conf import settings
# from apps.host.models import ChargingStation

# @shared_task
# def update_charging_stations():
#     gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

#     locations = [
#         (40.7128, -74.0060),   # New York City
#         (34.0522, -118.2437),  # Los Angeles
#         (41.8781, -87.6298),   # Chicago
#         (29.7604, -95.3698),   # Houston
#         (33.4484, -112.0740),  # Phoenix
#         (39.9526, -75.1652),   # Philadelphia
#         (32.7767, -96.7970),   # Dallas
#         (37.7749, -122.4194),  # San Francisco
#         (47.6062, -122.3321),  # Seattle
#         (25.7617, -80.1918),   # Miami
#     ]

#     radius = 50000

#     for loc in locations:
#         results = gmaps.places_nearby(
#             location=loc,
#             radius=radius,
#             type='electric_vehicle_charging_station'
#         )

#         for place in results.get('results', []):
#             name = place.get('name')
#             address = place.get('vicinity')
#             lat = place['geometry']['location']['lat']
#             lng = place['geometry']['location']['lng']

#             ChargingStation.objects.update_or_create(
#                 name=name,
#                 defaults={
#                     'address': address,
#                     'latitude': lat,
#                     'longitude': lng,
#                 }
#             )
#     return "✅ Monthly Charging Station Update Completed"
