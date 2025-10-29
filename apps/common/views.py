from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import *
from .serializers import *
from django.core.mail import EmailMessage
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings


# Create your views here.
@swagger_auto_schema(method='get', tags=['Common'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def get_privacy_policy(request):
    policy = PrivacyPolicy.objects.first()
    serializer = PrivacyPolicySerializer(policy)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(method='get', tags=['Common'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def get_terms_conditions(request):
    terms = TermsConditions.objects.first()
    serializer = TermsConditionsSerializer(terms)
    return Response(serializer.data, status=status.HTTP_200_OK)
    

@swagger_auto_schema(method='post', request_body=SupportSerializer, tags=['Common'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def support(request):
    serializer = SupportSerializer(data=request.data)

    if serializer.is_valid():
        email_address = serializer.validated_data["email"]
        subject = serializer.validated_data["subject"]
        message = serializer.validated_data['message']

        try:
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.DEFAULT_FROM_EMAIL],
                reply_to=[email_address],
            )
            email.send(fail_silently=False)
            return Response({"message": "Your support request has been submitted successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "Something went wrong. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"error": "Invalid input. Please check your data."}, status=status.HTTP_400_BAD_REQUEST)

    