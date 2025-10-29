import random
from django.utils.crypto import get_random_string
from django.core.management.base import BaseCommand
from apps.host.models import ChargingStation, ChargerDetail  

class Command(BaseCommand):
    help = "Update or create ChargerDetail records with random/default values for all ChargingStations"

    def handle(self, *args, **kwargs):
        stations = ChargingStation.objects.all()

        if not stations.exists():
            self.stdout.write(self.style.WARNING("⚠️ No Charging Stations found in database."))
            return

        for index, station in enumerate(stations, start=1):
            scanner_image = f"stations/scanner_{get_random_string(6).upper()}.jpg" 
            charger_type = random.choice(['type_a', 'type_b', 'chademo', 'ccs'])
            charger_level = random.choice(['Level 1', 'Level 2', 'Level 3'])
            price_per_hour = round(random.uniform(1.0, 10.0), 2)
            price_per_kwh = round(random.uniform(0.2, 2.0), 2)
            available = random.choice([True, False])
            available_24_7 = random.choice([True, False])

            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            available_days = random.sample(days, random.randint(3, 7))

            options = ['Extended for 5 Min', 'Extended for 10 Min', 'Extended for 25 Min']
            extended_charging_options = random.sample(options, random.randint(1, 2))

            # Create or update ChargerDetail record for each station
            ChargerDetail.objects.update_or_create(
                station=station,
                defaults={
                    'scanner_image': scanner_image,
                    'charger_type': charger_type,
                    'charger_level': charger_level,
                    'price_per_hour': price_per_hour,
                    'price_per_kwh': price_per_kwh,
                    'available': available,
                    'available_24_7': available_24_7,
                    'available_days': available_days,
                    'extended_charging_options': extended_charging_options,
                    'image': 'stations/default.jpg',
                }
            )

            self.stdout.write(self.style.SUCCESS(f"✅ Updated/Created ChargerDetail for {station.name}"))

        self.stdout.write(self.style.SUCCESS("🎉 All ChargerDetail records updated successfully!"))