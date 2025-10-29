from django.contrib import admin
from apps.subscriptions.models import SubscriptionPlan, Subscription

class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'plan_type', 'price', 'billing_cycle', 'max_chargers', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'plan_type')
    list_filter = ('is_active', 'billing_cycle')
    ordering = ('-created_at',)

admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)




class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'status', 'start_date', 'end_date',  'created_at')
    search_fields = ('user__full_name', 'plan__name')
    ordering = ('-created_at',)

admin.site.register(Subscription, SubscriptionAdmin)