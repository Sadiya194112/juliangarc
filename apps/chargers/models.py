from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


User = get_user_model()


class Charger(models.Model):
    CHARGER_TYPES = (
        ('level_1', 'Level 1 (120V)'),
        ('level_2', 'Level 2 (240V)'),
        ('dc_fast', 'DC Fast Charging'),
        ('tesla_wall', 'Tesla Wall Connector'),
        ('tesla_supercharger', 'Tesla Supercharger'),
        ('chademo', 'CHAdeMO'),
        ('ccs', 'CCS (Combined Charging System)'),
    )
    
    CONNECTOR_TYPES = (
        ('j1772', 'J1772'),
        ('tesla', 'Tesla'),
        ('chademo', 'CHAdeMO'),
        ('ccs1', 'CCS1'),
        ('ccs2', 'CCS2'),
        ('type2', 'Type 2'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('pending_approval', 'Pending Approval'),
        ('rejected', 'Rejected'),
    )
    
    # Basic Information
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chargers')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    charger_type = models.CharField(max_length=20, choices=CHARGER_TYPES)
    connector_types = models.JSONField(default=list)  # Multiple connector types
    
    # Location
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Specifications
    power_output = models.DecimalField(max_digits=5, decimal_places=2, help_text="Power output in kW")
    max_charging_speed = models.DecimalField(max_digits=5, decimal_places=2, help_text="Max charging speed in kW")
    
    # Pricing
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    daily_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Availability
    is_24_7 = models.BooleanField(default=False)
    available_hours = models.JSONField(default=dict, blank=True)  # Store availability schedule
    
    # Features
    amenities = models.JSONField(default=list, blank=True)  # WiFi, restroom, food, etc.
    parking_type = models.CharField(max_length=50, default='outdoor')  # outdoor, covered, garage
    accessibility_features = models.JSONField(default=list, blank=True)
    
    # Images
    main_image = models.ImageField(upload_to='chargers/main/', blank=True, null=True)
    
    # Status and Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_approval')
    is_verified = models.BooleanField(default=False)
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Metrics
    total_bookings = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'))
    total_reviews = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.host.username}"
    
    @property
    def is_featured(self):
        """Check if charger has active featured listing"""
        from subscriptions.models import FeaturedListing
        from django.utils import timezone
        
        return FeaturedListing.objects.filter(
            charger=self,
            is_active=True,
            is_paid=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).exists()


class ChargerImage(models.Model):
    """Additional images for chargers"""
    charger = models.ForeignKey(Charger, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='chargers/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.charger.name}"


class ChargerAvailability(models.Model):
    """Track charger availability for specific dates"""
    charger = models.ForeignKey(Charger, on_delete=models.CASCADE, related_name='availability_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['charger', 'date', 'start_time']
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.charger.name} - {self.date} {self.start_time}-{self.end_time}"
