from django.urls import path
from apps.host.views import add_charger, chargers_list, charging_station_list, host_booking_list


urlpatterns = [
    path('add-charger/', add_charger, name='add_charger'),
    path('my-chargers/', chargers_list, name='my_chargers'),
    path('stations/', charging_station_list, name='charging_station_list'),
    
    path('bookings/', host_booking_list, name='host-bookings')
    
    # path('list-chargers/', list_chargers, name='list_chargers')
    # path('stations/<int:pk>/detail/', charging_station_detail, name='station_detail'),
    # path('chargers/change-status/', change_status, name='change_charger_status'),
    
    #Stripe Express Account
    # path('create-stripe-account/', create_stripe_account, name='create_stripe_account'),
]