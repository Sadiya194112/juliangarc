from django.urls import path
from apps.bookings.views import create_booking, submit_review, start_charging_session, stop_charging_session, get_booking_details, charging_activity, get_charging_info, pay_for_booking, stripe_webhook
from apps.bookings.irin_views import payment_success, payment_cancel, get_charging_history, charging_history_detail, booking_list

urlpatterns = [
    path('create-booking/', create_booking, name='create-booking'),
    path('get-booking/<int:booking_id>/details/', get_booking_details, name='booking-details'),
    path('booking-list/', booking_list, name='booking-list'),
    path('start-charging/', start_charging_session, name='start-charging'),
    path('charging-activity/', charging_activity, name='charging-activity'),
    path('finish-charging/', stop_charging_session, name='finish-charging'),
    path('charging/<int:booking_id>/information/', get_charging_info, name='charging-information'),
    path('pay-for-booking/', pay_for_booking, name='pay-for-booking'),
    path('submit-review/', submit_review, name='submit-review'),
    
    
    # Didn't check stripe-webhook
    # path('stripe-webhook/', stripe_webhook, name='stripe-webhook'),

    path("payment-success/", payment_success, name="payment_success"),
    path("payment-cancel/", payment_cancel, name="payment_cancel"),
    
    path('charging-history/', get_charging_history, name='charging-history'),
    path('charging/<int:booking_id>/history/', charging_history_detail, name='charging-history')
]
