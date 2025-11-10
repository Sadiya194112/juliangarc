from django.urls import path  
from apps.Stripe.views import create_host_payout, setup_stripe_connect, get_host_payouts, get_user_payments, stripe_webhook, payment_success, payment_cancel, stripe_onboarding_refresh, stripe_onboarding_return, host_withdraw_now, host_earnings_and_payouts

urlpatterns = [
    # path('create-checkout-session/', create_checkout_session, name='create-checkout-session'),
    
        
    #Stripe Express Account
    path('stripe-connect/setup/', setup_stripe_connect, name='setup_stripe_connect'),
    # path('payout/', create_host_payout, name='create_host_payout'),
    path('host-withdraw-now/', host_withdraw_now, name='host-withdraw-now'),
    path('earnings-payout/', host_earnings_and_payouts, name='earnings-payout'),
    path('my-payouts/', get_host_payouts, name='get_host_payouts'),
    path('my-payments/', get_user_payments, name='get_user_payments'),
    
    path('success/', payment_success, name='payment_success'),
    path('cancel/', payment_cancel, name='payment_cancel'),
    
    path('webhook/', stripe_webhook, name='stripe_webhook'),
    
    
    path("onboarding/refresh/", stripe_onboarding_refresh, name="stripe_onboarding_refresh"),
    path("onboarding/return/", stripe_onboarding_return, name="stripe_onboarding_return"),

    
]
