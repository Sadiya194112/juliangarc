from decimal import Decimal 
from rest_framework import serializers
from apps.host.models import ChargingStation, Charger
from apps.bookings.serializers import *


class ChargerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Charger
        fields = [
            'id',
            'scanner_image',
            'charger_type',
            'charger_level',
            'price_per_hour',
            'price_per_kwh',
            'available',
            'available_24_7',
            'available_days',
            'extended_charging_options',
            'status',
            'image'
        ]


class ChargingStationSerializer(serializers.ModelSerializer):
    host = serializers.StringRelatedField(read_only=True)
    details = serializers.JSONField(write_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ChargingStation
        fields = [
            'id', 'host', 'station_name', 'location_area', 'address', 'status', 'status_display',
            'opening_time', 'closing_time', 'latitude', 'longitude', 
            'google_place_id', 'image', 'details', 'reviews',
            'average_rating', 'review_count', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        details_data = validated_data.pop('details', {})

        # Convert booleans properly if passed as strings
        for key in ['available', 'available_24_7']:
            if key in details_data and isinstance(details_data[key], str):
                details_data[key] = details_data[key].lower() == 'true'

        # Convert numeric string values to Decimal
        for key in ['price_per_hour', 'price_per_kwh']:
            if key in details_data and isinstance(details_data[key], str):
                details_data[key] = Decimal(details_data[key])

        # Get current user from context
        request = self.context.get('request')
        host = request.user if request and request.user.is_authenticated else None

        # Create station linked to host
        station = ChargingStation.objects.create(host=host, **validated_data)

        # Create associated charger details
        ChargerDetail.objects.create(station=station, **details_data)

        return station