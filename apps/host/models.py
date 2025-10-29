from django.db import models
from apps.accounts.models import User
from django.utils import timezone
import datetime
from apps.driver.models import PlugType


class ChargingStation(models.Model):
    STATION_STATUS_CHOICES = [
        ('OP', 'Open'),
        ('CL', 'Closed'),
        ('MA', 'In Maintenance'),
    ]
    host = models.OneToOneField(User, on_delete=models.CASCADE, related_name='charging_station')
    station_name = models.CharField(max_length=200, verbose_name="Station Name")
    location_area = models.CharField(max_length=255, verbose_name="Location Area/Expressway")
    address = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=2, choices=STATION_STATUS_CHOICES, default='OP')
    opening_time = models.TimeField(default=datetime.time(9, 0))
    closing_time = models.TimeField(default=datetime.time(22, 0))
    latitude = models.FloatField()
    longitude = models.FloatField()
    google_place_id = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='station_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 2)
        return 0

    @property
    def review_count(self):
        return self.reviews.count()

    @property
    def is_currently_open(self):
        if self.status != 'OP':
            return False
        current_time = timezone.localtime(timezone.now()).time()
        return self.opening_time <= current_time < self.closing_time

    class Meta:
        verbose_name = "Charging Station"
        verbose_name_plural = "Charging Stations"
        ordering = ['station_name']

    def __str__(self):
        return self.station_name


class ChargerType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    voltage = models.IntegerField(null=True, blank=True)
    amperage = models.IntegerField(null=True, blank=True)
    is_fast_charge = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    
class ConnectorType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
    

class Charger(models.Model):
    RATE_TYPE_CHOICES = (
        ('hour', 'Per Hour'),
        ('kwh', 'Per kWh'),
    )
    name = models.CharField(max_length=50)
    station = models.ForeignKey(ChargingStation, on_delete=models.CASCADE, related_name='chargers')
    charger_type = models.ForeignKey(ChargerType, on_delete=models.PROTECT, related_name='chargers')
    plug_types = models.ManyToManyField(PlugType, related_name='chargers')
    connector_types = models.ManyToManyField(ConnectorType, related_name='chargers')
    mode = models.CharField(
        max_length=10,
        choices=RATE_TYPE_CHOICES,
        default='hour'
    )
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    available = models.BooleanField(default=True)
    open_24_7 = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.station.station_name})"