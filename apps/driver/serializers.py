from rest_framework import serializers
from .models import PlugType, Vehicle, UserVehicle


# Create your serializers here.
# class DriverVehicleSerializer(serializers.ModelSerializer):
#     user = serializers.StringRelatedField(read_only=True)

#     class Meta:
#         model = DriverVehicle
#         fields = [
#             'id',
#             'user',
#             "vehicle_type",
#             'vehicle_name',
#             'registration_number',
#             'plug_type',
#             'battery_type',
#             'battery_capacity',
#             'image',
#         ]

#     def validate_registration_number(self, value):
#         user = self.context['request'].user
#         if DriverVehicle.objects.filter(user=user, registration_number=value).exists():
#             raise serializers.ValidationError("You already added a vehicle with this registration number.")
#         return value


# --- PlugType Serializer ---
class PlugTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlugType
        fields = ['id', 'name']


# --- Vehicle Serializer ---
class VehicleSerializer(serializers.ModelSerializer):
    supported_plugs = PlugTypeSerializer(many=True, read_only=True)
    is_default = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            'id', 'name', 'vehicle_type', 'battery_type',
            'units_per_time', 'supported_plugs',
            'battery_capacity', 'charging_time', 'image', 'is_default'
        ]

    def get_is_default(self, obj):
        """
        This method will return whether the vehicle is the default vehicle for the current user.
        """
        user = self.context['request'].user 
        try:
            user_vehicle = UserVehicle.objects.get(user=user, vehicle=obj)
            return user_vehicle.is_default
        except UserVehicle.DoesNotExist:
            return False 


class UserVehicleSerializer(serializers.ModelSerializer):
    vehicle_details = serializers.SerializerMethodField(read_only=True)
    selected_plug_name = serializers.CharField(source='selected_plug.name', read_only=True)

    # Custom vehicle fields
    custom_vehicle_name = serializers.CharField(required=False, allow_blank=True)
    vehicle_type = serializers.ChoiceField(choices=Vehicle.VEHICLE_TYPES, required=False)
    battery_type = serializers.CharField(required=False, allow_blank=True)
    supported_plugs_custom = serializers.PrimaryKeyRelatedField(
        queryset=PlugType.objects.all(), many=True, required=False
    )

    # Make vehicle optional
    vehicle = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(), required=False, allow_null=True
    )
    is_default = serializers.BooleanField(default=False)


    class Meta:
        model = UserVehicle
        fields = [
            'id', 'registration_number',
            'vehicle', 'vehicle_details',
            'selected_plug', 'selected_plug_name',
            'units_value', 'time_value',
            'custom_vehicle_name', 'vehicle_type',
            'battery_type', 'supported_plugs_custom', 'is_default'
        ]
        read_only_fields = ['id', 'vehicle_details', 'selected_plug_name']

    def get_vehicle_details(self, obj):
        vehicle = obj.vehicle
        plugs = vehicle.supported_plugs.all()
        return {
            "id": vehicle.id,
            "name": vehicle.name,
            "vehicle_type": vehicle.vehicle_type,
            "battery_type": vehicle.battery_type,
            "units_per_time": vehicle.units_per_time,
            "supported_plugs": [{"id": p.id, "name": p.name} for p in plugs],
            "battery_capacity": str(vehicle.battery_capacity),
            "charging_time": str(vehicle.charging_time),
            "image": vehicle.image.url if vehicle.image else None
        }

    def validate(self, data):
        vehicle = data.get('vehicle')
        plug = data.get('selected_plug')
        custom_name = data.get('custom_vehicle_name')
        registration_number = data.get('registration_number')

        if not registration_number:
            raise serializers.ValidationError({"registration_number": "This field is required."})

        # Master vehicle validation
        if vehicle:
            if not plug:
                raise serializers.ValidationError({"selected_plug": "This field is required for master vehicle."})
            if not vehicle.supported_plugs.filter(id=plug.id).exists():
                raise serializers.ValidationError({"selected_plug": "Selected plug is not supported by this vehicle."})

        # Custom vehicle validation
        elif custom_name:
            vehicle_type = data.get('vehicle_type')
            battery_type = data.get('battery_type')
            supported_plugs_custom = data.get('supported_plugs_custom')

            if not vehicle_type or not battery_type:
                raise serializers.ValidationError(
                    "vehicle_type and battery_type are required for custom vehicle."
                )
            if not supported_plugs_custom or len(supported_plugs_custom) == 0:
                raise serializers.ValidationError(
                    "At least one supported plug is required for custom vehicle."
                )
            if not plug or plug.id not in [p.id for p in supported_plugs_custom]:
                raise serializers.ValidationError(
                    {"selected_plug": "Selected plug must be in supported plugs."}
                )

        else:
            raise serializers.ValidationError(
                "Either select a master vehicle or provide a custom vehicle."
            )

        return data
    
    
    def create(self, validated_data):
        custom_name = validated_data.pop('custom_vehicle_name', None)

        if custom_name:
            plugs = validated_data.pop('supported_plugs_custom')
            vehicle = Vehicle.objects.create(
                name=custom_name,
                vehicle_type=validated_data.pop('vehicle_type'),
                battery_type=validated_data.pop('battery_type')
            )
            vehicle.supported_plugs.set(plugs)
            validated_data['vehicle'] = vehicle

        is_default = validated_data.get('is_default', False)
        if is_default:
            UserVehicle.objects.filter(user=validated_data['user']).update(is_default=False)
        
        user_vehicle = super().create(validated_data)

        if is_default:
            user_vehicle.is_default = True
            user_vehicle.save()

        return user_vehicle