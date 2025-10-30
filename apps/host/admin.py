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



# class ChargerDetailAdmin(admin.ModelAdmin):
#     list_display = ['id', 'station_id_display', 'station', 'charger_type', 'charger_level', 'price_per_hour', 'price_per_kwh', 'available', 'available_24_7', 'available_days', 'extended_charging_options', 'image']
    
#     def station_id_display(self, obj):
#         return obj.station.id  

#     station_id_display.short_description = 'Station ID' 
# admin.site.register(ChargerDetail, ChargerDetailAdmin)


admin.site.register(ChargerType)
admin.site.register(Charger)
