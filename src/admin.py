from apps.accounts.admin_dashboard import CustomAdminSite

admin_site = CustomAdminSite(name='custom_admin')

# Register your models normally:
from apps.accounts.models import User, Profile
from apps.bookings.models import Booking
from apps.host.models import ChargingStation
from apps.Stripe.models import Payment

admin_site.register(User)
admin_site.register(Profile)
admin_site.register(Booking)
admin_site.register(ChargingStation)
admin_site.register(Payment)
