from django.urls import path
from apps.driver.irin_views import contact_us
from apps.driver.views import vehicle_list, plug_type_list, add_user_vehicle, user_vehicle_list, user_vehicle_detail, user_vehicle_update, user_vehicle_delete, nearby_stations, get_charger_types


urlpatterns = [
    # --- Vehicle and PlugType ---
    path('vehicles/', vehicle_list, name='vehicle-list'),
    path('plug-types/', plug_type_list, name='plug-type-list'),
    path('charger-types/', get_charger_types, name='get_charger_types'),

    # --- User Vehicle CRUD ---
    path('user-vehicles/add/', add_user_vehicle, name='add-user-vehicle'),
    path('user-vehicles/', user_vehicle_list, name='user-vehicle-list'),
    path('user-vehicles/<int:pk>/detail/', user_vehicle_detail, name='user-vehicle-detail'),
    path('user-vehicles/<int:pk>/update/', user_vehicle_update, name='user-vehicle-update'),
    path('user-vehicles/<int:pk>/delete/', user_vehicle_delete, name='user-vehicle-delete'),
    path('stations/nearby/', nearby_stations, name='nearby-stations'),
    # path('station/<int:pk>/nearby/', nearby_station_detail, name='nearby-station-detail'),
    path('contact-us/', contact_us, name='contact-us'),

]