import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.host.models import ChargingStation

User = get_user_model()

class Command(BaseCommand):
    help = "Create multiple hosts and one charging station for each host"

    def handle(self, *args, **kwargs):
        hosts_data = [
            {
                "full_name": "Sadiya",
                "email": "kazisadiya1@example.com",
                "phone": "+8801912345001",
                "station_name": "PowerUp California",
                "location_area": "Midtown Expressway",
                "latitude": 34.05,
                "longitude": -118.24,
            },
            {
                "full_name": "Julian",
                "email": "julianhost@example.com",
                "phone": "+8801912345002",
                "station_name": "VoltZone New York",
                "location_area": "Downtown Manhattan",
                "latitude": 40.7128,
                "longitude": -74.0060,
            },
            {
                "full_name": "Rahim",
                "email": "rahimhost@example.com",
                "phone": "+8801912345003",
                "station_name": "ChargeHub Texas",
                "location_area": "Houston Central",
                "latitude": 29.7604,
                "longitude": -95.3698,
            },
        ]

        for data in hosts_data:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "full_name": data["full_name"],
                    "phone": data["phone"],
                    "role": "host",
                },
            )
            user.set_password("12345678")
            user.save()

            # Check if station already exists for this host
            if hasattr(user, "charging_station"):
                self.stdout.write(f"⚠️ Host {user.email} already has a station.")
                continue

            # Create charging station
            station = ChargingStation.objects.create(
                host=user,
                station_name=data["station_name"],
                location_area=data["location_area"],
                latitude=data["latitude"],
                longitude=data["longitude"],
                status="OP",
                opening_time=datetime.time(9, 0),
                closing_time=datetime.time(22, 0),
            )

            self.stdout.write(
                self.style.SUCCESS(f"✅ Created Host: {user.email} and Station: {station.station_name}")
            )

        self.stdout.write(self.style.SUCCESS("🎉 All hosts and stations created successfully!"))