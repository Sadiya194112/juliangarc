from django.contrib import admin
from apps.driver.models import PlugType, Vehicle, UserVehicle


# Register your models here.
admin.site.register(PlugType)
admin.site.register(Vehicle)


@admin.register(UserVehicle)
class UserVehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'vehicle', 'registration_number']


