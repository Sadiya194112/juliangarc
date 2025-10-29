from decimal import Decimal
from django.db import models
from apps.accounts.models import User
from apps.bookings.models import Booking



class Payment(models.Model):
    PAYMENT_TYPES = (
        ('booking', 'Booking Payment'),
        ('subscription', 'Subscription Payment'),
        ('featured_listing', 'Featured Listing'),
        ('day_pass', 'Day Pass'),
        ('booking_extension', 'Booking Extension'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    host_payout = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Stripe Information
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    client_secret = models.CharField(max_length=255, blank=True, null=True)
    

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    # subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, null=True, blank=True)
    # featured_listing = models.ForeignKey(FeaturedListing, on_delete=models.CASCADE, null=True, blank=True)
    

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Payment #{self.id} - {self.user.full_name} - ${self.amount}"



class Payout(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    

    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    

    stripe_payout_id = models.CharField(max_length=255, unique=True)
    stripe_account_id = models.CharField(max_length=255)  # Host's Stripe Connect account
    

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
  
    bookings = models.ManyToManyField('bookings.Booking', related_name='payouts')
    

    created_at = models.DateTimeField(auto_now_add=True)
    expected_arrival_date = models.DateTimeField(null=True, blank=True)
    arrival_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Payout #{self.id} - {self.host.username} - ${self.amount}"
    
    
    
    