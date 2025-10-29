from django.urls import path
from apps.accounts.views import *

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('google-login/', google_login, name='google_login'),
    path('apple-login/', apple_login, name='apple_login'),
    
    path('forgot-password/', forget_password, name='forgot-password'),
    path('verify-otp/', verify_otp, name='verify-otp'),
    path('reset-password/', reset_password, name='change-password'),  
    path('change-password/', change_password, name='change-password'),
    
    
    # Profile Management
    path('get-profile/', user_profile, name='get-profile'),
    path('profile/update/', update_profile, name='update-profile'),
    # path('users/<int:pk>/detail/', user_detail, name='user_detail'),

]
