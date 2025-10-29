import stripe
import logging
from django.conf import settings
from rest_framework import status
from apps.Stripe.models import Payment
from rest_framework.response import Response


logger = logging.getLogger(__name__)

def setup_stripe_payment(booking, user):
    """
    Handles Stripe customer creation, payment intent, and payment record.
    """
    try:
        # Ensure user has Stripe customer ID
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
            )
            user.stripe_customer_id = customer['id']
            user.save()

        # Create payment intent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(booking.total_amount * 100),
            currency='usd',
            customer=user.stripe_customer_id,
            metadata={
                'booking_id': booking.id,
                'driver_id': user.id,
                'host_id': booking.host.id,
                'charger_id': booking.charger.id,
            },
            transfer_data={
                'destination': booking.host.stripe_account_id,
                'amount': int(booking.subtotal * 100),
            } if booking.host.stripe_account_id else None,
        )

        # Save payment info
        Payment.objects.create(
            user=user,
            payment_type='booking',
            amount=booking.total_amount,
            platform_fee=booking.platform_fee,
            host_payout=booking.subtotal,
            stripe_payment_intent_id=payment_intent.id,
            client_secret=payment_intent.client_secret,
            booking=booking
        )

        # Return the client secret for frontend use
        return payment_intent.client_secret

    except Exception as e:
        raise Exception(str(e))
    
    