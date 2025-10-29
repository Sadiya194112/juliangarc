from django.urls import path
from apps.bookings.views import create_booking, submit_review


urlpatterns = [
    path('create-booking/', create_booking, name='create-booking'),
    path('submit-review/', submit_review, name='submit-review'),
]
