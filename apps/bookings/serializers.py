from rest_framework import serializers
from apps.bookings.models import Booking, Review



class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            'station',
            'charger',
            'booking_date',
            'start_time',
            'end_time',
            'plug'
        ]
        
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'user', 'plug', 'vehicle', 'subtotal', 'platform_fee', 'total_amount', 'is_paid', 'status', 'booking_date', 'payment_date']
   


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['charging_station', 'rating', 'comment']

    def validate(self, data):
        request = self.context['request']
        station = data.get('charging_station')

        # ✅ Prevent duplicate review by the same user for the same station
        if Review.objects.filter(charging_station=station, reviewer=request.user).exists():
            raise serializers.ValidationError("You have already submitted a review for this station.")

        return data

    def create(self, validated_data):
        request = self.context['request']

        review = Review.objects.create(
            charging_station=validated_data['charging_station'],
            reviewer=request.user,
            rating=validated_data['rating'],
            comment=validated_data.get('comment', ''),
        )
        return review




   
class BookingHostViewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name')
    vehicle_name = serializers.SerializerMethodField()  # First vehicle of the user
    charger_type = serializers.CharField(source='charger.charger_type')
    plug_type = serializers.SerializerMethodField()  # Get the selected plug from the user's vehicle
    booking_date = serializers.DateField()
    status = serializers.CharField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    station_name = serializers.CharField(source='station.station_name')
    location_area = serializers.CharField(source='station.location_area')
    user_picture = serializers.ImageField(source='user.picture', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'user_name',
            'user_picture',
            'vehicle_name',
            'charger_type',
            'plug_type',
            'booking_date',
            'status',
            'start_time',
            'end_time',
            'station_name',
            'location_area'
        ]
    
    def get_vehicle_name(self, obj):
        # Ensure vehicle exists before accessing its name
        if obj.vehicle:
            return obj.vehicle.name
        return None  # If vehicle is None, return None or an appropriate fallback value
    
    def get_plug_type(self, obj):
        # Check if the vehicle exists, then access the UserVehicle to get the selected_plug
        if obj.vehicle:
            # Get the first UserVehicle related to this vehicle and user
            user_vehicle = obj.vehicle.uservehicle_set.filter(user=obj.user).first()
            if user_vehicle and user_vehicle.selected_plug:
                return user_vehicle.selected_plug.name  # Return the plug name
        return None  # If no selected_plug or vehicle, return None or an appropriate fallback value


    
    
class BookingCompletedSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name')
    user_picture = serializers.ImageField(source='user.picture', read_only=True) 

    vehicle_name = serializers.CharField(source='user.vehicles.first.vehicle.name')  # First vehicle of the user
    charger_type = serializers.CharField(source='charger.charger_type')
    plug_type = serializers.CharField(source='user.vehicles.first.selected_plug.name')  # Get the selected plug from the first vehicle of the user
    booking_date = serializers.DateField()
    status = serializers.CharField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    station_name = serializers.CharField(source='station.station_name')
    location_area = serializers.CharField(source='station.location_area')

    reviews = ReviewSerializer(source='station.reviews', many=True, read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id',
            'user_name',
            'user_picture',
            'vehicle_name',
            'charger_type',
            'plug_type',
            'booking_date',
            'status',
            'start_time',
            'end_time',
            'station_name', 
            'location_area',
            'reviews'
        ]


