from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from apps.subscriptions.models import SubscriptionPlan, Subscription


# ----------------------------
# Subscription Plan Admin
# ----------------------------
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(ModelAdmin):
    list_display = [
        "id", "name", "plan_type", "price", "billing_cycle",
        "max_chargers", "is_active", "created_at"
    ]
    search_fields = ["name", "plan_type"]
    list_filter = ["is_active", "billing_cycle"]
    ordering = ["-created_at"]
    list_per_page = 25

    def colored_active(self, obj):
        color = "#22c55e" if obj.is_active else "#ef4444"
        label = "Active" if obj.is_active else "Inactive"
        return format_html(
            f'<span style="background-color:{color}; color:white; padding:3px 8px; border-radius:6px; font-size:12px;">{label}</span>'
        )
    colored_active.short_description = "Status"

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Plan Name", "sortable": True},
                {"name": "Plan Type", "sortable": True},
                {"name": "Price", "sortable": True},
                {"name": "Billing Cycle", "sortable": True},
                {"name": "Max Chargers", "sortable": True},
                {"name": "Active", "sortable": True},
                {"name": "Created", "sortable": True},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Subscription Plan Details",
            "layout": [
                ("name", "plan_type"),
                ("price", "billing_cycle"),
                ("max_chargers", "is_active"),
                ("created_at", "updated_at"),
            ],
            "save_button": "Save Plan",
        },
        "buttons": [
            {"name": "Add New Plan", "icon": "plus", "url": "subscriptionplan:add"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config


# ----------------------------
# Subscription Admin
# ----------------------------
@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = [
        "id", "user", "plan", "colored_status",
        "start_date", "end_date", "created_at"
    ]
    search_fields = ["user__full_name", "plan__name"]
    ordering = ["-created_at"]
    list_filter = ["status", "plan"]
    list_per_page = 25

    def colored_status(self, obj):
        colors = {
            "active": "#22c55e",
            "expired": "#9ca3af",
            "cancelled": "#ef4444",
            "trialing": "#3b82f6",
            "paused": "#facc15",
        }
        color = colors.get(obj.status.lower(), "#9ca3af")
        return format_html(
            f'<span style="background-color:{color}; color:white; padding:3px 8px; border-radius:6px; font-size:12px;">{obj.get_status_display()}</span>'
        )
    colored_status.short_description = "Status"

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "User", "sortable": True},
                {"name": "Plan", "sortable": True},
                {"name": "Status", "sortable": True},
                {"name": "Start Date", "sortable": True},
                {"name": "End Date", "sortable": True},
                {"name": "Created At", "sortable": True},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Subscription Details",
            "layout": [
                ("user", "plan"),
                ("status",),
                ("start_date", "end_date"),
                ("created_at",),
            ],
            "save_button": "Save Subscription",
        },
        "buttons": [
            {"name": "Add Subscription", "icon": "plus", "url": "subscription:add"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config
