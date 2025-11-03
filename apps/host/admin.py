from django.contrib import admin
from apps.host.models import ChargingStation, ChargerType, Charger


@admin.register(ChargingStation)
class ChargingStationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'station_name', 'host', 'location_area',
        'address', 'status', 
        'opening_time', 'closing_time',
        'latitude', 'longitude', 'google_place_id'
    ]
    list_filter = ['status', 'location_area']
    search_fields = ['station_name', 'address', 'google_place_id']
    readonly_fields = ['created_at', 'updated_at', 'average_rating', 'review_count']
    fieldsets = (
        ('Basic Information', {
            'fields': ('station_name', 'host', 'location_area', 'address', 'status', 'image')
        }),
        ('Location Details', {
            'fields': ('latitude', 'longitude', 'google_place_id')
        }),
        ('Timing Information', {
            'fields': ('opening_time', 'closing_time')
        }),
        ('Reviews & Ratings', {
            'fields': ('average_rating', 'review_count')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at')
        }),
    )



@admin.register(Charger)
class ChargerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'station__id', 'station', 'charger_type', 'mode', 'price']
    
admin.site.register(ChargerType)
