# from django.contrib import admin
# from apps.host.models import ChargingStation, ChargerDetail

# class ChargingStationAdmin(admin.ModelAdmin):
#     list_display = ['id', 'address', 'latitude', 'longitude', 'google_place_id']

# admin.site.register(ChargingStation, ChargingStationAdmin)



# class ChargerDetailAdmin(admin.ModelAdmin):
#     list_display = ['id', 'station_id_display', 'station', 'charger_type', 'charger_level', 'price_per_hour', 'price_per_kwh', 'available', 'available_24_7', 'available_days', 'extended_charging_options', 'image']
    
#     def station_id_display(self, obj):
#         return obj.station.id  

#     station_id_display.short_description = 'Station ID' 
# admin.site.register(ChargerDetail, ChargerDetailAdmin)