from apps.bookings.models import Booking
from apps.common.models import Notification

def create_booking_notification(booking, status_value):
    Notification.objects.create(
        user=booking.user,
        message=f"Your booking has been {status_value} by {booking.station.station_name}."
    )
