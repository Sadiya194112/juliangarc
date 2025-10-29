import stripe
from django.conf import settings

def create_stripe_checkout_session(user, plan):
    """
    Create Stripe Checkout Session for subscription plan
    """
    # Create Stripe Customer if not exists
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            name=user.get_full_name() if hasattr(user, 'get_full_name') else user.username
        )
        user.stripe_customer_id = customer.id
        user.save()

    # Create Stripe Checkout Session with metadata
    session = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        payment_method_types=['card'],
        mode='subscription',
        line_items=[{
            'price': plan.stripe_price_id,
            'quantity': 1,
        }],
        success_url='http://127.0.0.1:8000/api/v1/stripe/success/',
        cancel_url='http://127.0.0.1:8000/api/v1/stripe/cancel/',
        metadata={
            'user_id': str(user.id),
            'plan_id': str(plan.id)
        }
    )

    return session