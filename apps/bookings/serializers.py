from rest_framework import serializers
from apps.bookings.models import Booking, Review



class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            'charger',
            'start_datetime',
            'end_datetime',
            # 'vehicle_info',
            # 'special_instructions',
            'booking_type',
        ]
        
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'driver', 'host', 'subtotal', 'platform_fee', 'total_amount', 'is_paid', 'payment_date']
        

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
