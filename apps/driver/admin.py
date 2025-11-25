from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from apps.driver.models import PlugType, Vehicle, UserVehicle


# ----------------------------
# PlugType Admin
# ----------------------------
@admin.register(PlugType)
class PlugTypeAdmin(ModelAdmin):
    list_display = ["id", "name", "image_preview", "is_fast_charge"]
    search_fields = ["name"]
    list_per_page = 20

    # Adding the image preview in the admin panel for PlugType
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" style="border-radius:6px;"/>', obj.image.url)
        return "—"
    image_preview.short_description = "Image Preview"

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Plug Name", "sortable": True},
                {"name": "Image", "sortable": False},  # Image field added
                {"name": "Fast Charge", "sortable": False},  # Fast charge status
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Plug Type Details",
            "layout": [
                ("name",),
                ("image",),  # Display image in edit form as well
                ("is_fast_charge",),
            ],
            "save_button": "Save Plug Type",
        },
        "buttons": [
            {"name": "Add Plug Type", "icon": "plus", "url": "plugtype:add"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config


# ----------------------------
# Vehicle Admin
# ----------------------------
@admin.register(Vehicle)
class VehicleAdmin(ModelAdmin):
    list_display = ["id", "name", "vehicle_type", "battery_type", "image_preview", "plug_types_display"]
    search_fields = ["name", "vehicle_type", "battery_type"]
    list_filter = ["vehicle_type", "battery_type"]
    list_per_page = 25

    # Display image preview for vehicles
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" style="border-radius:6px;"/>', obj.image.url)
        return "—"
    image_preview.short_description = "Image Preview"

    # Display the plug types associated with each vehicle
    def plug_types_display(self, obj):
        plug_names = [plug.name for plug in obj.supported_plugs.all()]
        return ", ".join(plug_names) if plug_names else "No plugs available"
    plug_types_display.short_description = "Plug Types"

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Name", "sortable": True},
                {"name": "Vehicle Type", "sortable": True},
                {"name": "Battery Type", "sortable": True},
                {"name": "Image Preview", "sortable": False},
                {"name": "Plug Types", "sortable": False},  # Add column for plug types
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Vehicle Information",
            "layout": [
                ("name", "vehicle_type"),
                ("battery_type",),
                ("image",),
                ("supported_plugs",),  # Display the plugs in the edit form
            ],
            "save_button": "Save Vehicle",
        },
        "buttons": [
            {"name": "Add Vehicle", "icon": "plus", "url": "vehicle:add"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config


# ----------------------------
# User Vehicle Admin
# ----------------------------
@admin.register(UserVehicle)
class UserVehicleAdmin(ModelAdmin):
    list_display = ["id", "user", "vehicle", "registration_number"]
    search_fields = ["user__email", "vehicle__name", "registration_number"]
    list_filter = ["vehicle"]
    list_per_page = 25

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "User", "sortable": True},
                {"name": "Vehicle", "sortable": True},
                {"name": "Registration Number", "sortable": True},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "User Vehicle Details",
            "layout": [
                ("user", "vehicle"),
                ("registration_number",),
            ],
            "save_button": "Save User Vehicle",
        },
        "buttons": [
            {"name": "Assign Vehicle", "icon": "plus", "url": "uservehicle:add"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config
