from datetime import timedelta
from apps.accounts.models import User
from django.core.management.base import BaseCommand
from apps.driver.models import PlugType, Vehicle, UserVehicle

class Command(BaseCommand):
    help = 'Add vehicle, plug type, and user vehicle data'

    def handle(self, *args, **kwargs):
        # Create some PlugType data
        plug1, created = PlugType.objects.get_or_create(name='Type 1', is_fast_charge=True)
        plug2, created = PlugType.objects.get_or_create(name='Type 2', is_fast_charge=False)

        # Print if the PlugType was created or already exists
        self.stdout.write(f"PlugType 'Type 1' created: {created}")
        self.stdout.write(f"PlugType 'Type 2' created: {created}")

        # Create Vehicle data
        vehicle1, created = Vehicle.objects.get_or_create(
            name='Tesla Model S',
            vehicle_type='CAR',
            battery_type='Lithium-ion',
            units_per_time='kW/h',
            battery_capacity=75.0,
            charging_time=timedelta(hours=1.5)
        )
        vehicle2, created = Vehicle.objects.get_or_create(
            name='Yamaha R15',
            vehicle_type='BIKE',
            battery_type='Lead-acid',
            units_per_time='kW/h',
            battery_capacity=12.0,
            charging_time=timedelta(hours=0.5)
        )

        # Print if the Vehicle was created or already exists
        self.stdout.write(f"Vehicle 'Tesla Model S' created: {created}")
        self.stdout.write(f"Vehicle 'Yamaha R15' created: {created}")

        # Create a user (if not already created)
        user, created = User.objects.get_or_create(full_name='johndoe', email='john@example.com')
        if created:
            user.set_password('password123')  # Ensure the user has a password
            user.save()

        # Print if the user was created or already exists
        self.stdout.write(f"User 'johndoe' created: {created}")

        # Create UserVehicle data
        user_vehicle1, created = UserVehicle.objects.get_or_create(
            user=user,
            vehicle=vehicle1,
            registration_number='TS-1234',
            selected_plug=plug1,
            units_value=10.0,
            time_value=timedelta(hours=1)
        )
        user_vehicle2, created = UserVehicle.objects.get_or_create(
            user=user,
            vehicle=vehicle2,
            registration_number='YAM-5678',
            selected_plug=plug2,
            units_value=5.0,
            time_value=timedelta(hours=0.5)
        )

        # Print if the UserVehicle was created or already exists
        self.stdout.write(f"UserVehicle 'TS-1234' created: {created}")
        self.stdout.write(f"UserVehicle 'YAM-5678' created: {created}")
