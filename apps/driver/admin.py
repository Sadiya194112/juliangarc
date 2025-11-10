from django.contrib import admin
from apps.driver.models import PlugType, Vehicle, UserVehicle


# Register your models here.
admin.site.register(PlugType)



@admin.register(UserVehicle)
class UserVehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'vehicle', 'registration_number']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'vehicle_type', 'battery_type', 'image']