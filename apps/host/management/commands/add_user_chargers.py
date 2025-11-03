import os
import qrcode
import uuid
from django.core.files import File
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from apps.host.models import ChargingStation, Charger, ChargerType, ConnectorType, PlugType

User = get_user_model()

class Command(BaseCommand):
    help = "Add chargers for user kazisadiya1@example.com"

    def handle(self, *args, **kwargs):
        email = "kazisadiya1@example.com"

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {email} not found"))
            return
        
        stations = ChargingStation.objects.filter(host=user)

        if not stations.exists():
            self.stdout.write(self.style.ERROR("No stations found for this user"))
            return
        
        # Create base types
        charger_type, _ = ChargerType.objects.get_or_create(
            name="Fast Charger",
            defaults={"voltage": 480, "amperage": 125, "is_fast_charge": True}
        )

        connector_ccs, _ = ConnectorType.objects.get_or_create(name="CCS Combo")
        connector_type2, _ = ConnectorType.objects.get_or_create(name="CHAdeMO")

        plug1, _ = PlugType.objects.get_or_create(name="Type-2 Plug")
        plug2, _ = PlugType.objects.get_or_create(name="CHAdeMO Plug")

        for station in stations:
            for i in range(1, 4):  # 3 chargers per station
                unique_code = str(uuid.uuid4())

                charger = Charger.objects.create(
                    name=f"Super Charger {i}",
                    scanner_code=unique_code,
                    station=station,
                    charger_type=charger_type,
                    price=50,
                    extended_price_per_unit=15,
                    mode='hour',
                )

                charger.plug_types.add(plug1, plug2)
                charger.connector_types.add(connector_ccs, connector_type2)

                # ✅ Generate QR code & attach to scanner_image
                img = qrcode.make(unique_code)
                img_path = os.path.join(settings.MEDIA_ROOT, f"charger_scanners/{unique_code}.png")
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                img.save(img_path)

                with open(img_path, "rb") as f:
                    charger.scanner_image.save(f"{unique_code}.png", File(f), save=True)

                self.stdout.write(self.style.SUCCESS(f"Added charger: {charger.name} to {station.station_name}"))

        self.stdout.write(self.style.SUCCESS("✅ All chargers added successfully!"))
