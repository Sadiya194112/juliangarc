from django.urls import path
from apps.subscriptions.views import create_subscription_payment, get_subscription_plans, get_user_subscriptions

urlpatterns = [
    path('plans/', get_subscription_plans, name='get_subscription_plans'),
    path('user-subscriptions/', get_user_subscriptions, name='get_user_subscriptions'),
    path('subscribe-to-plan/', create_subscription_payment, name='create_subscription_payment'),

]
