from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="My API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@myapi.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    path('api/v1/', include([
        path('', include('apps.accounts.urls')),
        path('bookings/', include('apps.bookings.urls')),
        path('driver/', include('apps.driver.urls')),
        path('host/', include('apps.host.urls')),
        path('common/', include('apps.common.urls')),
        path('chat/', include('apps.features.chat.urls')),
        path('stripe/', include('apps.Stripe.urls')),
        path('subscriptions/', include('apps.subscriptions.urls')),
    ])),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
