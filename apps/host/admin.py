from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from apps.host.models import ChargingStation, ChargerType, Charger, ConnectorType


# ----------------------------
# Charging Station Admin
# ----------------------------
@admin.register(ChargingStation)
class ChargingStationAdmin(ModelAdmin):
    list_display = [
        "id", "station_name", "host", "location_area", "address",
        "status", "opening_time", "closing_time", "average_rating", "review_count"
    ]
    list_filter = ["status", "location_area"]
    search_fields = ["station_name", "address", "google_place_id"]
    readonly_fields = ["created_at", "updated_at", "average_rating", "review_count"]
    list_per_page = 20

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" style="border-radius:6px;"/>', obj.image.url)
        return "—"
    image_preview.short_description = "Image Preview"

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Station Name", "sortable": True},
                {"name": "Host", "sortable": True},
                {"name": "Location", "sortable": True},
                {"name": "Status", "sortable": True},
                {"name": "Opening Time", "sortable": True},
                {"name": "Closing Time", "sortable": True},
                {"name": "Rating", "sortable": True},
                {"name": "Reviews", "sortable": True},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Charging Station Details",
            "layout": [
                ("station_name", "host"),
                ("location_area", "address"),
                ("status", "image"),
                ("latitude", "longitude", "google_place_id"),
                ("opening_time", "closing_time"),
                ("average_rating", "review_count"),
                ("created_at", "updated_at"),
            ],
            "save_button": "Save Charging Station",
        },
        "buttons": [
            {"name": "Add Station", "icon": "plus", "url": "chargingstation:add"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config


# ----------------------------
# Charger Admin
# ----------------------------
@admin.register(Charger)
class ChargerAdmin(ModelAdmin):
    list_display = ["id", "name", "station", "charger_type", "mode", "price"]
    list_filter = ["charger_type", "mode"]
    search_fields = ["name", "station__station_name", "charger_type__name"]
    list_per_page = 25

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Name", "sortable": True},
                {"name": "Station", "sortable": True},
                {"name": "Charger Type", "sortable": True},
                {"name": "Mode", "sortable": True},
                {"name": "Price", "sortable": True},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Charger Details",
            "layout": [
                ("name", "station"),
                ("charger_type", "mode"),
                ("price",),
            ],
            "save_button": "Save Charger",
        },
        "buttons": [
            {"name": "Add Charger", "icon": "plus", "url": "charger:add"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config


# ----------------------------
# Charger Type Admin
# ----------------------------
@admin.register(ChargerType)
class ChargerTypeAdmin(ModelAdmin):
    list_display = ["id", "name", "description"]
    search_fields = ["name", "description"]
    list_per_page = 25

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Charger Type", "sortable": True},
                {"name": "Description", "sortable": False},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Charger Type Details",
            "layout": [
                ("name",),
                ("description",),
            ],
            "save_button": "Save Charger Type",
        },
        "buttons": [
            {"name": "Add Charger Type", "icon": "plus", "url": "chargertype:add"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config




# ----------------------------
# Connector Type Admin
# ----------------------------

@admin.register(ConnectorType)
class ConnectorTypeAdmin(ModelAdmin):
    list_display = ["id", "name", "description"]
    search_fields = ["name", "description"]
    list_per_page = 25

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Connector Type", "sortable": True},
                {"name": "Description", "sortable": False},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Connector Type Details",
            "layout": [
                ("name",),
                ("description",),
            ],
            "save_button": "Save Connector Type",
        },
        "buttons": [
            {"name": "Add Connector Type", "icon": "plus", "url": "connector:add"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config