from django.contrib import admin
from apps.bookings.models import Booking, Review

# Register your models here.
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'station', 'charger', 'status', 'is_paid', 'start_time', 'end_time', 'created_at')
    list_filter = ('status', 'created_at', 'station', 'charger')
    readonly_fields = ('created_at', 'updated_at')  

    search_fields = ('user__email', 'user__full_name', 'station__station_name', 'charger__name')

admin.site.register(Booking, BookingAdmin)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'charging_station', 'reviewer', 'rating', 'comment']


# class ReviewImageInline(admin.TabularInline):
#     model = ReviewImage
#     extra = 1  # Number of extra blank image slots
#     readonly_fields = ['created_at']
#     fields = ['image', 'created_at']


# # Admin for Review
# @admin.register(Review)
# class ReviewAdmin(admin.ModelAdmin):
#     list_display = ('id', 'charging_station__station_name', 'reviewer__full_name', 'rating', 'created_at')
#     list_filter = ('rating', 'created_at', 'charging_station')
#     search_fields = ('reviewer__full_name', 'charging_station__station_name', 'charging_station__location_area', 'comment')
#     inlines = [ReviewImageInline]

    # def charging_station_name(self, obj):
    #     return obj.charging_station.station_name
    # charging_station_name.short_description = "Station Name"

    # def reviewer_name(self, obj):
    #     return obj.reviewer.full_name
    # reviewer_name.short_description = "Reviewer"
