from datetime import timedelta
from rest_framework import status
from django.utils import timezone
from django.utils.timezone import now
from apps.accounts.models import User
from apps.accounts.utils import send_email
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
import uuid
from .apple_auth import *
from django.core.exceptions import ValidationError
from apps.accounts.utils import get_tokens_for_user
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import permission_classes, authentication_classes, api_view
from apps.accounts.serializers import (UserRegistrationSerializer, UserSerializer, 
    LoginSerializer, ForgetPasswordSerializer, 
    VerifyOTPSerializer, ResetPasswordSerializer, 
    UserProfileSerializer, UserUpdateSerializer, 
    ChangePasswordSerializer, AppleLoginSerializer,
    GoogleLoginSerializer
)


@swagger_auto_schema(method='post', request_body=UserRegistrationSerializer, tags=['Auth'])
@api_view(['POST'])
def signup(request):
    serializer = UserRegistrationSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        email = serializer.validated_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            return Response({"error": "Email is already registered."}, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save(email=email)
    
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        
        return Response({
            "message": "User registered successfully.",
            "access_token": str(access),
            "refresh_token": str(refresh),
            "data": UserSerializer(user, context={'request': request}).data            
            }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', request_body=LoginSerializer, tags=['Auth'])
@api_view(['POST'])
def login(request):
    email = request.data.get('email', '').strip().lower()
    serializer = LoginSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email'].lower()
    password = serializer.validated_data['password']


    user = authenticate(request, email=email, password=password)

    if user is None:
        return Response({"message": "Invalid email or password"},
                        status=status.HTTP_401_UNAUTHORIZED)


    token = get_tokens_for_user(user)
    return Response({
        "message": "Login successful",
        "access_token": token['access_token'],
        "refresh_token": token['refresh_token'],
        "data": UserSerializer(user, context={'request': request}).data
    }, status=status.HTTP_200_OK)
    
    
    
@swagger_auto_schema(method='post', request_body=ForgetPasswordSerializer, tags=['Auth'])
@api_view(['POST'])
def forget_password(request):
    serializer = ForgetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email'].strip().lower()
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"message": "Email not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        otp = send_email(email)
    except Exception as e:
        return Response({"message": "Failed to send OTP", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    user.otp = otp
    user.otp_expiry = timezone.now() + timedelta(minutes=5)
    user.save()

    return Response({"message": "OTP sent to your email"}, status=status.HTTP_200_OK)




@swagger_auto_schema(method='post', request_body=VerifyOTPSerializer, tags=['Auth'])
@api_view(['POST'])
def verify_otp(request):
    serializer = VerifyOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data.get('email').strip().lower()
    otp = serializer.validated_data.get('otp').strip()

    try:
        user = User.objects.get(email=email, otp=otp)

    
        if user.otp_expiry and now() > user.otp_expiry:
            otp = send_email(user.email)
            user.otp = otp
            user.otp_expiry = timezone.now() + timedelta(minutes=3)
            user.save()
            raise ValidationError({"error": "Looks like that code's a bit too old — it expired after 10 minutes. I just sent you a fresh one, so check your email(and maybe spam)."})

        if user.otp != otp:
            raise ValidationError({"error": "Invalid OTP. Please try again."})

        else:
            user.otp = None
            user.otp_expiry = None
            user.is_active = True
            user.is_verified = True
            user.save()

            return Response({
                "message": "OTP verified successfully.",
                "data": UserSerializer(user, context={'request': request}).data
            }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            "error": "If that email's in the system, I've already sent a OTP verification message your way. Go check your inbox(and maybe your spam folder, just in case)."
        }, status=status.HTTP_404_NOT_FOUND)
        



@swagger_auto_schema(method='post', request_body=ResetPasswordSerializer, tags=['Auth'])
@api_view(['POST'])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"success": True, "message": "Password reset successfully."},
            status=status.HTTP_200_OK,
        )
    return Response(
        {"success": False, "errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )
    

@swagger_auto_schema(method='post', request_body=ChangePasswordSerializer, tags=['Auth'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def change_password(request):
    user = request.user
    serializer = ChangePasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    current_password = serializer.validated_data.get('old_password')
    new_password = serializer.validated_data.get('new_password')
    confirm_password = serializer.validated_data.get('confirm_password')

    if not user.check_password(current_password):
        return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

    if new_password != confirm_password:
        return Response({"error": "New password and confirm password do not match."}, status=status.HTTP_400_BAD_REQUEST)

    if len(new_password) < 8:
        return Response({"error": "New password must be at least 8 characters long."}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def user_profile(request):
    serializer = UserProfileSerializer(request.user)
    return Response({"message": "Profile retrieved successfully.", "data": serializer.data}, status=status.HTTP_200_OK)



@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def update_profile(request):
    user = request.user
    serializer = UserUpdateSerializer(user, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Profile updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)
    return Response({"detail": "Invalid data. Please check your input."}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', tags=['Auth'])
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data['refresh']
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logout successful'}, status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({"error": "Invalid or expired refresh token"}, status=status.HTTP_400_BAD_REQUEST)
    

@swagger_auto_schema(method='post', request_body=GoogleLoginSerializer, tags=['Auth'])
@api_view(['POST'])
def google_login(request):
    serializer = GoogleLoginSerializer(data=request.data)
    if serializer.is_valid():
        user, created = serializer.create_or_get_user()
        tokens = get_tokens_for_user(user)
        return Response({
            "message": "Login successful",
            **tokens,
            "data": UserSerializer(user).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@swagger_auto_schema(method='post', request_body=AppleLoginSerializer, tags=['Auth'])
@api_view(["POST"])
def apple_login(request):
    serializer = AppleLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    id_token = serializer.validated_data["id_token"]

    try:
        decoded = verify_apple_token(id_token)
    except Exception as e:
        return Response(
            {"detail": f"Invalid id_token: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Extract user info
    apple_sub = decoded.get("sub")
    email = decoded.get("email")
    name = decoded.get("name")

    # Fallbacks if missing
    if not email:
        email = f"{apple_sub}@appleuser.com"
    if not name:
        name = f"AppleUser-{uuid.uuid4().hex[:6]}"

    # Create or get user
    user, created = User.objects.get_or_create(
        email=email,
        defaults={"name": name}
    )
    
    if created:
        user.apple_id = apple_sub
        user.set_unusable_password()
        user.save()

    # Generate JWT tokens
    tokens = get_tokens_for_user(user)

    return Response({
        "message": "Login successful",
        **tokens,
        "data": UserSerializer(user, context={'request': request}).data
    }, status=status.HTTP_200_OK)