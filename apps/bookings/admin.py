# from django.contrib import admin
# from apps.bookings.models import Booking, Review

# # Register your models here.
# class BookingAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'station', 'charger', 'status', 'is_paid', 'start_time', 'end_time', 'created_at')
#     list_filter = ('status', 'created_at', 'station', 'charger')
#     readonly_fields = ('created_at', 'updated_at')  

#     search_fields = ('user__email', 'user__full_name', 'station__station_name', 'charger__name')

# admin.site.register(Booking, BookingAdmin)


# @admin.register(Review)
# class ReviewAdmin(admin.ModelAdmin):
#     list_display = ['id', 'charging_station', 'reviewer', 'rating', 'comment']







from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.bookings.models import Booking, Review


# Booking Admin Customization
class BookingAdmin(ModelAdmin):
    list_display = (
        'id', 'user', 'station', 'station__host', 'charger', 'status', 'is_paid', 'start_time', 'end_time', 'created_at'
    )
    list_filter = ('status', 'created_at', 'station', 'charger')
    readonly_fields = ('created_at', 'updated_at')  
    search_fields = ('user__email', 'user__full_name', 'station__station_name', 'charger__name')

    # Unfold UI Customizations
    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "Booking ID", "sortable": True},
                {"name": "User", "sortable": True},
                {"name": "Station", "sortable": True},
                {"name": "Charger", "sortable": True},
                {"name": "Status", "sortable": True},
                {"name": "Paid", "sortable": False},
                {"name": "Start Time", "sortable": True},
                {"name": "End Time", "sortable": True},
                {"name": "Created At", "sortable": True}
            ],
            "search_enabled": True
        },
        "edit_form": {
            "title": "Edit Booking",
            "layout": [
                ("user", "station", "charger"),
                ("status", "is_paid", "booking_date"),
                ("start_time", "end_time"),
                ("hourly_rate", "subtotal", "platform_fee", "total_amount"),
                ("check_in_time", "check_out_time", "actual_duration"),
            ],
            "save_button": "Save Booking"
        },
        "buttons": [
            {"name": "Mark as Paid", "icon": "check-circle", "url": "mark_as_paid"},
            {"name": "View Booking Details", "icon": "eye", "url": "view_details"}
        ]
    }

    def unfold_ui_config(self):
        return self.unfold_config


admin.site.register(Booking, BookingAdmin)


# Review Admin Customization
@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ['id', 'charging_station', 'reviewer', 'rating', 'comment']
    
    # Unfold UI Customizations for ReviewAdmin
    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "Review ID", "sortable": True},
                {"name": "Charging Station", "sortable": True},
                {"name": "Reviewer", "sortable": True},
                {"name": "Rating", "sortable": True},
                {"name": "Comment", "sortable": False},
            ],
            "search_enabled": True
        },
        "edit_form": {
            "title": "Edit Review",
            "layout": [
                ("charging_station", "reviewer"),
                ("rating", "comment")
            ],
            "save_button": "Save Review"
        },
        "buttons": [
            {"name": "View Review", "icon": "eye", "url": "view_review"}
        ]
    }

    def unfold_ui_config(self):
        return self.unfold_config
