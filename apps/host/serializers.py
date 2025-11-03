import io
import uuid
import qrcode
import base64
from rest_framework import serializers
from apps.accounts.models import User
from django.core.files.base import ContentFile
from apps.bookings.serializers import ReviewSerializer
from apps.host.models import Charger, ChargingStation
from rest_framework.exceptions import ValidationError



# class ChargerCreateSerializer(serializers.ModelSerializer):
#     station_latitude = serializers.FloatField(write_only=True)
#     station_longitude = serializers.FloatField(write_only=True)
#     station_address = serializers.CharField(write_only=True)
#     station_id = serializers.IntegerField(write_only=True)

#     class Meta:
#         model = Charger
#         fields = [
#             'id', 'name', 'charger_type', 'mode', 'price',
#             'open_24_7', 'available', 'is_active',
#             'extended_time_unit', 'extended_price_per_unit',
#             'station_id', 'station_latitude', 'station_longitude', 'station_address',
#         ]

#     def create(self, validated_data):
#         station_id = validated_data.pop('station_id')
#         latitude = validated_data.pop('station_latitude')
#         longitude = validated_data.pop('station_longitude')
#         address = validated_data.pop('station_address')

#         station = ChargingStation.objects.get(id=station_id)
#         station.latitude = latitude
#         station.longitude = longitude
#         station.address = address
#         station.save()
        

#         # scanner_code generate
#         scanner_code = str(uuid.uuid4())
#         validated_data['scanner_code'] = scanner_code

#         charger = Charger.objects.create(station=station, **validated_data)

#         qr = qrcode.QRCode(
#             version=1,
#             error_correction=qrcode.constants.ERROR_CORRECT_L,
#             box_size=10,
#             border=4,
#         )
#         qr.add_data(scanner_code)
#         qr.make(fit=True)
#         img = qr.make_image(fill_color="black", back_color="white")

#         buffer = io.BytesIO()
#         img.save(buffer, format='PNG')
#         file_name = f'charger_qr_{charger.id}.png'
#         charger.scanner_image.save(file_name, ContentFile(buffer.getvalue()), save=True)

#         return charger


class ChargerCreateSerializer(serializers.ModelSerializer):
    station_latitude = serializers.FloatField(write_only=True)
    station_longitude = serializers.FloatField(write_only=True)
    station_address = serializers.CharField(write_only=True)
    station_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Charger
        fields = [
            'id', 'name', 'charger_type', 'mode', 'price',
            'open_24_7', 'available', 'is_active',
            'extended_time_unit', 'extended_price_per_unit',
            'station_id', 'station_latitude', 'station_longitude', 'station_address',
        ]

    def create(self, validated_data):
        try:
            # Step 1: Extract station details
            station_id = validated_data.pop('station_id')
            latitude = validated_data.pop('station_latitude')
            longitude = validated_data.pop('station_longitude')
            address = validated_data.pop('station_address')

            # Step 2: Fetch the ChargingStation
            try:
                station = ChargingStation.objects.get(id=station_id)
            except ChargingStation.DoesNotExist:
                raise ValidationError(f"Charging Station with ID {station_id} does not exist.")

            # Step 3: Update the ChargingStation with new details
            station.latitude = latitude
            station.longitude = longitude
            station.address = address
            station.save()

            # Step 4: Generate scanner code
            scanner_code = str(uuid.uuid4())
            validated_data['scanner_code'] = scanner_code

            # Step 5: Create Charger instance
            charger = Charger.objects.create(station=station, **validated_data)

            # Step 6: Generate QR Code for the charger
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(scanner_code)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            # Step 7: Save the QR code as an image
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            file_name = f'charger_qr_{charger.id}.png'
            charger.scanner_image.save(file_name, ContentFile(buffer.getvalue()), save=True)

            # Return the created charger
            return charger

        except Exception as e:
            # Catch any other unexpected errors
            raise ValidationError(f"An error occurred: {str(e)}")
    
    

class ChargerSerializer(serializers.ModelSerializer):
    # qr_code = serializers.SerializerMethodField()

    class Meta:
        model = Charger
        fields = [
            "id", "name", "scanner_code", "scanner_image", "station",
            "charger_type", "plug_types", "connector_types",
            "mode", "price", "available", "open_24_7", "is_active"
        ]

    # def get_qr_code(self, obj):
    #     """scanner_image থেকে Base64 return করা"""
    #     if not obj.scanner_image:
    #         return None

    #     with obj.scanner_image.open('rb') as f:
    #         img_str = base64.b64encode(f.read()).decode()
    #     return f"data:image/png;base64,{img_str}"




class HostInfoSerializer(serializers.ModelSerializer):
    """Host basic info serializer (for nested field)"""
    class Meta:
        model = User
        fields = ["id", "full_name", "email", "phone"]

class ChargingStationSerializer(serializers.ModelSerializer):
    """Main serializer for charging stations"""
    host = HostInfoSerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = ChargingStation
        fields = [
            "id",
            "station_name",
            "location_area",
            "address",
            "latitude",
            "longitude",
            "status",
            "opening_time",
            "closing_time",
            "image",
            "average_rating",
            "host",
            "reviews",
        ]

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 2)
        return 0



# class ChargerDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Charger
#         fields = [
#             'id',
#             'scanner_image',
#             'charger_type',
#             'charger_level',
#             'price_per_hour',
#             'price_per_kwh',
#             'available',
#             'available_24_7',
#             'available_days',
#             'extended_charging_options',
#             'status',
#             'image'
#         ]


# class ChargingStationSerializer(serializers.ModelSerializer):
#     host = serializers.StringRelatedField(read_only=True)
#     details = serializers.JSONField(write_only=True)
#     reviews = ReviewSerializer(many=True, read_only=True)
#     average_rating = serializers.FloatField(read_only=True)
#     review_count = serializers.IntegerField(read_only=True)
#     status_display = serializers.CharField(source='get_status_display', read_only=True)

#     class Meta:
#         model = ChargingStation
#         fields = [
#             'id', 'host', 'station_name', 'location_area', 'address', 'status', 'status_display',
#             'opening_time', 'closing_time', 'latitude', 'longitude', 
#             'google_place_id', 'image', 'details', 'reviews',
#             'average_rating', 'review_count', 'created_at', 'updated_at'
#         ]

#     def create(self, validated_data):
#         details_data = validated_data.pop('details', {})

#         # Convert booleans properly if passed as strings
#         for key in ['available', 'available_24_7']:
#             if key in details_data and isinstance(details_data[key], str):
#                 details_data[key] = details_data[key].lower() == 'true'

#         # Convert numeric string values to Decimal
#         for key in ['price_per_hour', 'price_per_kwh']:
#             if key in details_data and isinstance(details_data[key], str):
#                 details_data[key] = Decimal(details_data[key])

#         # Get current user from context
#         request = self.context.get('request')
#         host = request.user if request and request.user.is_authenticated else None

#         # Create station linked to host
#         station = ChargingStation.objects.create(host=host, **validated_data)

#         # Create associated charger details
#         ChargerDetail.objects.create(station=station, **details_data)

#         return station






