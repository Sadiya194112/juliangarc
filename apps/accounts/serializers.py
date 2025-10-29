from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from apps.accounts.models import User, Profile
from apps.host.models import ChargingStation
import datetime



# class UserRegistrationSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, min_length=8)
#     confirm_password = serializers.CharField(write_only=True, min_length=8)
#     role = serializers.ChoiceField(choices=User.USER_TYPES)
#     terms_privacy = serializers.BooleanField(required=True)

#     class Meta:
#         model = User
#         fields = ['full_name', 'email', 'phone', 'role', 'password', 'confirm_password', 'terms_privacy']


#     def validate_terms_privacy(self, value):
#         if not value:
#             raise serializers.ValidationError("You must agree to the Terms & Privacy Policy to continue.")
#         return value
    
#     def validate(self, attrs):
#         if attrs['password'] != attrs['confirm_password']:
#             raise serializers.ValidationError("Passwords don't match")
#         return attrs
    
#     def create(self, validated_data):
#         validated_data.pop('confirm_password')
#         password = validated_data.pop('password')
#         user = User.objects.create_user(**validated_data)
#         user.set_password(password)
#         user.save()

#         if user.role == 'driver':
#             Profile.objects.create(user=user)
        
#         return user


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=User.USER_TYPES)
    terms_privacy = serializers.BooleanField(required=True)

    # Host-specific fields for ChargingStation
    station_name = serializers.CharField(max_length=200, required=False)
    location_area = serializers.CharField(max_length=255, required=False)
    address = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=ChargingStation.STATION_STATUS_CHOICES, default='OP', required=False)
    opening_time = serializers.TimeField(required=False, default=datetime.time(9, 0))
    closing_time = serializers.TimeField(required=False, default=datetime.time(22, 0))
    latitude = serializers.FloatField(required=False, default=0.0)
    longitude = serializers.FloatField(required=False, default=0.0)
    google_place_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'full_name', 'email', 'phone', 'role',
            'password', 'confirm_password', 'terms_privacy',
            'station_name', 'location_area', 'address', 'status',
            'opening_time', 'closing_time', 'latitude', 'longitude',
            'google_place_id', 'image'
        ]

    def validate_terms_privacy(self, value):
        if not value:
            raise serializers.ValidationError("You must agree to the Terms & Privacy Policy to continue.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")

        if attrs.get('role') == 'host':
            required_fields = ['station_name', 'location_area', 'latitude', 'longitude']
            for field in required_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').capitalize()} is required for hosts."})

        return attrs

    def create(self, validated_data):
        # Extract station-related fields
        station_data = {key: validated_data.pop(key, None) for key in [
            'station_name', 'location_area', 'address', 'status',
            'opening_time', 'closing_time', 'latitude', 'longitude',
            'google_place_id', 'image'
        ]}

        validated_data.pop('confirm_password')
        password = validated_data.pop('password')

        # Create user
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Role-specific profile
        if user.role == 'user':
            Profile.objects.create(user=user)
        elif user.role == 'host':
            ChargingStation.objects.create(host=user, **station_data)

        return user
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"error": "User with this email doesn't exist."})


        auth_user = authenticate(
            request=self.context.get('request'),
            username=email,   
            password=password
        )

        if auth_user is None:
            raise serializers.ValidationError({"error": "Invalid email or password."})

        data['user'] = auth_user
        return data



class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone', 'role', 'picture', 'is_online', 'last_seen', 'is_active']
    


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)
    


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone', 'picture']



class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, data):
        email = data["email"].lower()  
        data["email"] = email 
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})

        if not user.is_verified:
            raise serializers.ValidationError({"otp": "OTP verification required."})

        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        return data

    def save(self, **kwargs):
        user = User.objects.get(email=self.validated_data["email"])
        user.set_password(self.validated_data["password"])
        user.otp = None 
        user.otp_expiry = None
        user.is_verified = False 
        user.save()
        return user



class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['full_name', 'phone', 'picture']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords do not match.")
        return data
    
    
class GoogleLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField()
    picture = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def create_or_get_user(self):
        email = self.validated_data["email"]
        full_name = self.validated_data["full_name"]
        picture = self.validated_data.get("picture", "")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': full_name,
                'picture': picture
            }
        )

        return user, created
    
    
class AppleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=True, write_only=True)