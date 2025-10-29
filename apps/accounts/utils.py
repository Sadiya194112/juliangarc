import os
import random
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from apps.accounts.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework_simplejwt.tokens import RefreshToken


def generate_otp():
    return random.randint(1000, 9999)

def send_email(email):
    otp_code = generate_otp()
    subject = "Your OTP Verification Code from Voltly"
    
    html_message = render_to_string('accounts/otp_verification_email.html', {
        'otp_code': otp_code,
    })
    
    from_email = settings.EMAIL_HOST_USER

    print(from_email, email, otp_code)
    send_mail(
        subject,
        "",
        from_email,
        [email],
        html_message=html_message,
        fail_silently=False,
    )
    user = User.objects.get(email=email)
    user.otp = otp_code
    user.otp_expiry = timezone.now() + timedelta(minutes=3)
    user.save()

    return otp_code


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }
    