from decimal import Decimal
from django.db import models
from datetime import timedelta
from django.utils import timezone
from apps.accounts.models import User
from apps.host.models import Charger
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.host.models import ChargingStation
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError


class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    station = models.ForeignKey(ChargingStation, on_delete=models.CASCADE)
    charger = models.ForeignKey(Charger, on_delete=models.CASCADE)

    # Booking details
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    # Pricing
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    # Payment
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)

    # Tracking
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    actual_duration = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('charger', 'booking_date', 'start_time', 'end_time')

    def __str__(self):
        return f"Booking #{self.id} - {self.user.get_full_name()} on {self.booking_date} ({self.start_time}-{self.end_time})"

    @property
    def duration(self):
        """Duration of the booking in hours"""
        start_dt = datetime.combine(self.booking_date, self.start_time)
        end_dt = datetime.combine(self.booking_date, self.end_time)
        delta = end_dt - start_dt
        return Decimal(delta.total_seconds() / 3600)

    def clean(self):
        """Prevent overlapping bookings for the same charger"""
        overlapping = Booking.objects.filter(
            charger=self.charger,
            booking_date=self.booking_date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            status__in=['pending', 'confirmed', 'in_progress']
        ).exclude(id=self.id)

        if overlapping.exists():
            raise ValidationError("This time slot is already booked for this charger.")

    def save(self, *args, **kwargs):
        # Ensure validation runs
        self.clean()

        # Calculate pricing
        self.subtotal = self.hourly_rate * self.duration
        self.platform_fee = self.subtotal * Decimal('0.15')  # 15% fee
        self.total_amount = self.subtotal + self.platform_fee

        super().save(*args, **kwargs)

    @property
    def can_be_cancelled(self):
        """Booking can be cancelled 24 hours before start"""
        if self.status in ['completed', 'cancelled']:
            return False
        cancellation_deadline = datetime.combine(self.booking_date, self.start_time) - timedelta(hours=24)
        return timezone.now() < timezone.make_aware(cancellation_deadline)

    @property
    def is_upcoming(self):
        """Check if booking is upcoming"""
        now = timezone.now()
        start_dt = datetime.combine(self.booking_date, self.start_time)
        return start_dt > now and self.status in ['pending', 'confirmed']

    @property
    def is_active(self):
        """Check if booking is currently active"""
        now = timezone.now()
        start_dt = datetime.combine(self.booking_date, self.start_time)
        end_dt = datetime.combine(self.booking_date, self.end_time)
        return start_dt <= now <= end_dt and self.status in ['confirmed', 'in_progress']



class BookingStatusHistory(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=15)
    new_status = models.CharField(max_length=15)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Booking #{self.booking.id}: {self.old_status} → {self.new_status}"


class BookingExtension(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='extensions')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    original_end_time = models.DateTimeField()
    new_end_time = models.DateTimeField()
    additional_hours = models.DecimalField(max_digits=5, decimal_places=2)
    additional_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    is_approved = models.BooleanField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approved_extensions', null=True, blank=True)
    response_notes = models.TextField(blank=True)
    
    # Payment
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Extension for Booking #{self.booking.id} - {self.additional_hours}h"


# class Review(models.Model):
#     station = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
#     reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
#     reviewee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
#     rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])    
#     comment = models.TextField(blank=True)
#     image = models.ImageField(upload_to='review_images/', blank=True, null=True)
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     def __str__(self):
#         return f"Review by {self.reviewer.full_name} for {self.reviewee.full_name} - {self.rating} stars"


class Review(models.Model):
    charging_station = models.ForeignKey(
        ChargingStation,
        on_delete=models.CASCADE,
        related_name='reviews', null=True, blank=True
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_reviews'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('charging_station', 'reviewer')
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.reviewer.full_name} for {self.charging_station.station_name} - {self.rating}⭐"


# class ReviewImage(models.Model):
#     review = models.ForeignKey(
#         Review,
#         on_delete=models.CASCADE,
#         related_name='images'
#     )
#     image = models.ImageField(upload_to='review_images/')

#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Image for review {self.review.id}"