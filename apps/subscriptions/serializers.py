from rest_framework import serializers
from apps.subscriptions.models import SubscriptionPlan, Subscription



class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'plan_type', 'description', 'price', 'billing_cycle', 'features', 'max_chargers', 'max_reservations']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.IntegerField(write_only=True)
    class Meta:
        model = Subscription
        fields = ['id', 'user', 'plan', 'plan_id', 'status', 'start_date', 'end_date', 'trial_end',]
        read_only_fields = ('user', 'stripe_subscription_id', 'created_at', 'updated_at')
