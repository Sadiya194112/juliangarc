from django.contrib import admin
from apps.Stripe.models import Payment


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'payment_type', 'status', 'amount', 'platform_fee', 'host_payout', 'booking', 'stripe_payment_intent_id', 'stripe_charge_id')
    search_fields = ('user__full_name', 'stripe_payment_intent_id')
    list_filter = ('payment_type', 'created_at')

admin.site.register(Payment, PaymentAdmin)