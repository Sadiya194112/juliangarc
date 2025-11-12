from django.utils.html import format_html
from django.db import models
from unfold.sites import UnfoldAdminSite
from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.host.models import ChargingStation
from apps.Stripe.models import Payment


class CustomAdminSite(UnfoldAdminSite):
    site_header = "Wiiz.ai Admin Dashboard"
    site_title = "Wiiz.ai"
    index_title = "Dashboard Overview"

    def get_dashboard_context(self, request):
        total_users = User.objects.count()
        total_hosts = User.objects.filter(role="host").count()
        total_customers = User.objects.filter(role="user").count()
        total_bookings = Booking.objects.count()
        total_stations = ChargingStation.objects.count()
        total_payments = Payment.objects.count()
        total_revenue = Payment.objects.filter(status="succeeded").aggregate(total=models.Sum("amount"))["total"] or 0

        return {
            "cards": [
                {"title": "Total Users", "value": total_users, "icon": "users", "color": "#3b82f6"},
                {"title": "Hosts", "value": total_hosts, "icon": "briefcase", "color": "#22c55e"},
                {"title": "Customers", "value": total_customers, "icon": "user", "color": "#f59e0b"},
                {"title": "Charging Stations", "value": total_stations, "icon": "battery", "color": "#8b5cf6"},
                {"title": "Bookings", "value": total_bookings, "icon": "calendar", "color": "#ec4899"},
                {"title": "Revenue", "value": f"${total_revenue:,.2f}", "icon": "credit-card", "color": "#0ea5e9"},
            ],
            "charts": [
                {
                    "title": "User Roles Distribution",
                    "type": "pie",
                    "data": {
                        "labels": ["Hosts", "Users"],
                        "datasets": [{
                            "data": [total_hosts, total_customers],
                            "backgroundColor": ["#22c55e", "#3b82f6"]
                        }]
                    },
                },
                {
                    "title": "Payment Status Overview",
                    "type": "bar",
                    "data": {
                        "labels": ["Succeeded", "Pending", "Failed"],
                        "datasets": [{
                            "label": "Payments",
                            "data": [
                                Payment.objects.filter(status="succeeded").count(),
                                Payment.objects.filter(status="pending").count(),
                                Payment.objects.filter(status="failed").count(),
                            ],
                            "backgroundColor": ["#22c55e", "#facc15", "#ef4444"],
                        }]
                    },
                },
            ],
            "tables": [
                {
                    "title": "Recent Bookings",
                    "columns": ["User", "Station", "Status", "Created At"],
                    "rows": [
                        [
                            b.user.full_name,
                            b.station.station_name,
                            b.status.title(),
                            b.created_at.strftime("%Y-%m-%d"),
                        ]
                        for b in Booking.objects.order_by("-created_at")[:5]
                    ],
                },
                {
                    "title": "Latest Payments",
                    "columns": ["User", "Type", "Amount", "Status"],
                    "rows": [
                        [
                            p.user.full_name,
                            p.get_payment_type_display(),
                            f"${p.amount}",
                            p.status.title(),
                        ]
                        for p in Payment.objects.order_by("-created_at")[:5]
                    ],
                },
            ],
        }


# ✅ Instantiate it here so it can be imported in urls.py
admin_site = CustomAdminSite(name="custom_admin")
