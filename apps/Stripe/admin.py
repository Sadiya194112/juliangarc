from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from apps.Stripe.models import Payment, Payout


# ----------------------------
# Payment Admin
# ----------------------------
@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = [
        "id", "user", "payment_type", "colored_status",
        "amount", "platform_fee", "host_payout",
        "booking", "stripe_payment_intent_id", "created_at"
    ]
    search_fields = ["user__full_name", "stripe_payment_intent_id", "stripe_charge_id"]
    list_filter = ["payment_type", "status", "created_at"]
    readonly_fields = ["created_at", "updated_at", "processed_at"]
    list_per_page = 25

    # 🎨 Colored status badge
    def colored_status(self, obj):
        colors = {
            "pending": "#facc15",       # yellow
            "processing": "#3b82f6",    # blue
            "succeeded": "#22c55e",     # green
            "failed": "#ef4444",        # red
            "cancelled": "#a1a1aa",     # gray
            "refunded": "#6366f1",      # indigo
        }
        color = colors.get(obj.status, "#9ca3af")
        return format_html(
            f'<span style="background-color:{color}; color:white; padding:3px 8px; border-radius:6px; font-size:12px;">{obj.get_status_display()}</span>'
        )
    colored_status.short_description = "Status"

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "User", "sortable": True},
                {"name": "Type", "sortable": True},
                {"name": "Status", "sortable": True},
                {"name": "Amount", "sortable": True},
                {"name": "Platform Fee", "sortable": True},
                {"name": "Host Payout", "sortable": True},
                {"name": "Booking", "sortable": False},
                {"name": "Created At", "sortable": True},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Payment Details",
            "layout": [
                ("user", "payment_type", "status"),
                ("amount", "platform_fee", "host_payout"),
                ("booking",),
                ("stripe_payment_intent_id", "stripe_charge_id", "client_secret"),
                ("metadata",),
                ("created_at", "updated_at", "processed_at"),
            ],
            "save_button": "Save Payment",
        },
        "buttons": [
            {"name": "Add Payment", "icon": "plus", "url": "payment:add"},
            {"name": "View Stripe Dashboard", "icon": "external-link"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config


# ----------------------------
# Payout Admin
# ----------------------------
@admin.register(Payout)
class PayoutAdmin(ModelAdmin):
    list_display = [
        "id", "host", "colored_status", "amount",
        "currency", "stripe_payout_id", "expected_arrival_date", "arrival_date"
    ]
    search_fields = ["host__full_name", "stripe_payout_id", "stripe_account_id"]
    list_filter = ["status", "currency", "created_at"]
    readonly_fields = ["created_at"]
    list_per_page = 25

    # 🎨 Colored status badges
    def colored_status(self, obj):
        colors = {
            "pending": "#facc15",
            "in_transit": "#3b82f6",
            "paid": "#22c55e",
            "failed": "#ef4444",
            "cancelled": "#a1a1aa",
        }
        color = colors.get(obj.status, "#9ca3af")
        return format_html(
            f'<span style="background-color:{color}; color:white; padding:3px 8px; border-radius:6px; font-size:12px;">{obj.get_status_display()}</span>'
        )
    colored_status.short_description = "Status"

    unfold_config = {
        "list_display": {
            "columns": [
                {"name": "ID", "sortable": True},
                {"name": "Host", "sortable": True},
                {"name": "Status", "sortable": True},
                {"name": "Amount", "sortable": True},
                {"name": "Currency", "sortable": True},
                {"name": "Expected Arrival", "sortable": True},
                {"name": "Arrival", "sortable": True},
            ],
            "search_enabled": True,
        },
        "edit_form": {
            "title": "Payout Details",
            "layout": [
                ("host", "status", "currency"),
                ("amount",),
                ("stripe_payout_id", "stripe_account_id"),
                ("bookings",),
                ("expected_arrival_date", "arrival_date"),
                ("created_at",),
            ],
            "save_button": "Save Payout",
        },
        "buttons": [
            {"name": "Add Payout", "icon": "plus", "url": "payout:add"},
            {"name": "View Stripe Dashboard", "icon": "external-link"},
        ],
    }

    def unfold_ui_config(self):
        return self.unfold_config
