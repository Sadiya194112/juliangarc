from django.urls import path
from apps.common.views import get_privacy_policy, get_terms_conditions, support 


urlpatterns = [
    path('privacy-policy/', get_privacy_policy, name='get-privacy-policy'),
    path('terms-conditions/', get_terms_conditions, name='get-terms-conditions'),
    path('help-support/', support, name='help_support'),
]