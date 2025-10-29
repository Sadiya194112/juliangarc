import stripe
import logging
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from django.http import JsonResponse
from django.http import HttpResponse
from apps.accounts.models import User
from apps.Stripe.models import Payout
from apps.Stripe.models import Payment
from apps.bookings.models import Booking
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from apps.subscriptions.models import SubscriptionPlan, Subscription
from apps.Stripe.serializers import PayoutSerializer, PaymentSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes


logger = logging.getLogger(__name__)



@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def setup_stripe_connect(request):
    """Setup Stripe Connect account for a host."""
    if request.user.role != 'host':
        return Response({'error': 'Only hosts can set up Stripe Connect accounts.'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.user.stripe_account_id:
        return Response({'error': 'Stripe Connect account already exists.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Create a Stripe Connect account
        account = stripe.Account.create(
            type='express',
            country='US',
            email=request.user.email,
            capabilities={
                'card_payments': {'requested': True},
                'transfers': {'requested': True}
                
            },
        )
        
        # Save the Stripe account ID to the user profile
        request.user.stripe_account_id = account.id
        request.user.save()
        
        # Create account link for onboarding
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=f'{settings.FRONTEND_URL}/stripe/onboarding/refresh',
            return_url=f'{settings.FRONTEND_URL}/stripe/onboarding/return',
            type='account_onboarding',
        )
        return Response({
            'account_id': account.id,
            'onboarding_url': account_link.url
        }, status=status.HTTP_201_CREATED)
        
    except stripe.CardError as e:
        logger.error(f"Stripe Card Error during account setup: {e.user_message}")
        return Response({'error': e.user_message or "Your card was declined."}, status=status.HTTP_402_PAYMENT_REQUIRED)

    except stripe.InvalidRequestError as e:
        logger.error(f"Stripe Invalid Request during account setup: {e.user_message}")
        return Response({'error': e.user_message or "Invalid request to Stripe API."}, status=status.HTTP_400_BAD_REQUEST)

    except stripe.StripeError as e:
        logger.error(f"General Stripe error during account setup: {e.user_message}")
        return Response({'error': e.user_message or str(e)}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Unexpected error during account setup: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_host_payout(request):
    if request.user.role != 'admin':
        return Response({'error': 'Only admins can create host payouts.'}, status=status.HTTP_403_FORBIDDEN)    

    host_id = request.data.get('host_id')
    booking_ids = request.data.get('booking_ids', [])
    
    try:
        host = User.objects.get(id=host_id, role='host')
    except User.DoesNotExist:
        return Response({'error': 'Host not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    if not host.stripe_account_id:
        return Response({'error': 'Host does not have a Stripe account linked.'}, status=status.HTTP_400_BAD_REQUEST)
    
    
    # Get completed bookings for payout
    bookings = Booking.objects.filter(
        id__in=booking_ids,
        host=host,
        status='completed',
        is_paid=True
    )
    
    if not bookings.exists():
        return Response({'error': 'No valid completed bookings found for payout.'}, status=status.HTTP_400_BAD_REQUEST)     
    
    # Calculate total payout amount
    total_amount = sum(booking.subtotal for booking in bookings)
    
    try:
        # Create Stripe payout
        payout = stripe.Payout.create(
            amount=int(total_amount * 100),  # amount in cents
            currency='usd',
            stripe_account=host.stripe_account_id,
            metadata={
                'host_id': host.id,
                'booking_count': bookings.count(),
                'booking_ids': ','.join(str(b.id) for b in bookings)
            }
        )
        
        # Create payout record
        payout_record = Payout.objects.create(
            host=host,
            amount=total_amount,
            stripe_payout_id=payout.id,
            stripe_account_id=host.stripe_account_id,
            status='in_transit' if payout.status == 'in_transit' else 'pending'
        )
        
        # Associate bookings with payout
        payout_record.bookings.set(bookings)
        payout_record.save()
        
        return Response(PayoutSerializer(payout_record).data, status=status.HTTP_201_CREATED)

    except stripe.CardError as e:
        logger.error(f"Stripe Card Error during payout creation: {e.user_message}")
        return Response({'error': e.user_message or "Your card was declined."}, status=status.HTTP_402_PAYMENT_REQUIRED)

    except stripe.InvalidRequestError as e:
        logger.error(f"Stripe Invalid Request during payout creation: {e.user_message}")
        return Response({'error': e.user_message or "Invalid request to Stripe API."}, status=status.HTTP_400_BAD_REQUEST)

    except stripe.StripeError as e:
        logger.error(f"General Stripe error during payout creation: {e.user_message}")
        return Response({'error': e.user_message or str(e)}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Unexpected error during payout creation: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_host_payouts(request):
    """Get payouts for the authenticated host."""
    if request.user.role != 'host':
        return Response({'error': 'Only hosts can access their payouts.'}, status=status.HTTP_403_FORBIDDEN)
    
    payouts = Payout.objects.filter(host=request.user).order_by('-created_at')
    serializer = PayoutSerializer(payouts, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)




@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_payments(request):
    """Get payments for current user."""
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by payment type if provided
    payment_type = request.GET.get('payment_type')  
    if payment_type:
        payments = payments.filter(payment_type=payment_type)
    
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK) 



from stripe._error import SignatureVerificationError  

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except SignatureVerificationError:
        return HttpResponse(status=400)

    # Handle successful checkout
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        user_id = session['metadata'].get('user_id')
        plan_id = session['metadata'].get('plan_id')
        stripe_subscription_id = session.get('subscription')

        try:
            user = User.objects.get(id=user_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except (User.DoesNotExist, SubscriptionPlan.DoesNotExist):
            return JsonResponse({'error': 'User or Plan not found'}, status=400) 

        # Subscription তৈরি বা আপডেট করো
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            plan=plan,
            defaults={
                'stripe_subscription_id': stripe_subscription_id,
                'status': 'active',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=30) if plan.billing_cycle == 'monthly' else timezone.now() + timedelta(days=365)
            }
        )

        if not created:
            subscription.status = 'active'
            subscription.stripe_subscription_id = stripe_subscription_id
            subscription.end_date = timezone.now() + timedelta(days=30)
            subscription.save()

        print("✅ Subscription activated for:", user.email)

    return HttpResponse(status=200)



def payment_success(request):
    return JsonResponse({"message": "Payment successful!"})

def payment_cancel(request):
    return JsonResponse({"message": "Payment cancelled."})