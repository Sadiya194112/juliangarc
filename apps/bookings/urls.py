from django.urls import path
from apps.bookings.views import create_booking, submit_review, start_charging_session, stop_charging_session


urlpatterns = [
    path('create-booking/', create_booking, name='create-booking'),
    path('start-charging/', start_charging_session, name='start-charging'),
    path('finish-charging/', stop_charging_session, name='finish-charging'),
    path('submit-review/', submit_review, name='submit-review'),
]
