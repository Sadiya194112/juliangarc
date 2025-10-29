from rest_framework import serializers
from apps.Stripe.models import Payout, Payment


class PayoutSerializer(serializers.ModelSerializer):
    host_name = serializers.CharField(source='host.full_name', read_only=True)
    class Meta:
        model = Payout
        fields = ['id', 'host', 'amount', 'currency', 'status', 'stripe_account_id', 'stripe_payout_id', 'metadata', 'created_at', 'updated_at', 'processed_at']
        read_only_fields = ('host', 'stripe_payout_id', 'created_at', 'updated_at', 'processed_at')
        
    

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'user', 'amount', 'status', 'stripe_payment_intent_id', 'stripe_charge_id', 'booking', 'metadata', 'created_at', 'updated_at', 'processed_at']
        read_only_fields = ('user', 'stripe_payment_intent_id', 'stripe_charge_id', 'created_at', 'updated_at', 'processed_at')