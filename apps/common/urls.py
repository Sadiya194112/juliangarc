from django.urls import path
from .views import *


urlpatterns = [
    path('privacy-policy/', get_privacy_policy, name='get-privacy-policy'),
    path('terms-conditions/', get_terms_conditions, name='get-terms-conditions'),
    path('help-support/', support, name='help_support'),
]