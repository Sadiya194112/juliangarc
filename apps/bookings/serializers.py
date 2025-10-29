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
        fields = ['booking', 'rating', 'comment', 'image']

    def validate(self, data):
        request = self.context['request']
        booking = data.get('booking')

        # ✅ Ensure booking belongs to the driver and is completed
        if booking.driver != request.user or booking.status != 'completed':
            raise serializers.ValidationError("You can only review a completed booking that belongs to you.")

        # ✅ Prevent duplicate review
        if hasattr(booking, 'review'):
            raise serializers.ValidationError("You have already submitted a review for this booking.")

        return data

    def create(self, validated_data):
        request = self.context['request']
        booking = validated_data['booking']

        # ✅ Set reviewer and reviewee automatically
        review = Review.objects.create(
            booking=booking,
            reviewer=request.user,          # current driver
            reviewee=booking.host,      
            rating=validated_data['rating'],
            comment=validated_data.get('comment', ''),
            image=validated_data.get('image', None)
        )
        return review