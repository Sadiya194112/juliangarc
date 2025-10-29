from django.db import models
from apps.accounts.models import User
from datetime import timedelta


# class DriverVehicle(models.Model):
#     VEHICLE_TYPES = (
#         ('car', 'Car'),
#         ('bike', 'Bike'),
#     )
    
#     PLUG_TYPES = (
#         ('type_a', 'Type A'),
#         ('type_b', 'Type B'),
#         ('chademo', 'CHAdeMO'),
#         ('ccs', 'CCS Cable'),
#     )

#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
#     vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
#     vehicle_name = models.CharField(max_length=100)
#     registration_number = models.CharField(max_length=50, unique=True)
#     plug_type = models.CharField(max_length=50, choices=PLUG_TYPES)
#     battery_type = models.CharField(max_length=50, blank=True)
#     battery_capacity = models.CharField(max_length=50, blank=True)  
#     charging_time = models.CharField(max_length=50, blank=True)
#     image = models.ImageField(upload_to='vehicles/', blank=True, null=True)


#     def __str__(self):
#         return f"{self.vehicle_name} ({self.registration_number})"



# --- PlugType Model ---
class PlugType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_fast_charge = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# --- Vehicle Model (Master Data) ---
class Vehicle(models.Model):
    VEHICLE_TYPES = (
        ('CAR', 'Car'),
        ('BIKE', 'Bike'),
    )

    name = models.CharField(max_length=100, unique=True)
    vehicle_type = models.CharField(max_length=10, choices=VEHICLE_TYPES)
    battery_type = models.CharField(max_length=50)
    supported_plugs = models.ManyToManyField(PlugType)
    units_per_time = models.CharField(max_length=50, default='kW/h')
    battery_capacity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    charging_time = models.DurationField(default=timedelta(hours=4))
    image = models.ImageField(upload_to='vehicle_images/', null=True, blank=True)

    def __str__(self):
        return self.name


# --- UserVehicle Model (User-Specific Data) ---
class UserVehicle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    registration_number = models.CharField(max_length=20, unique=True)
    selected_plug = models.ForeignKey(PlugType, on_delete=models.PROTECT)
    units_value = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    time_value = models.DurationField(default=timedelta(hours=1))

    class Meta:
        unique_together = ('user', 'registration_number')

    def __str__(self):
        return f"{self.vehicle.name} ({self.registration_number})"
    

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"