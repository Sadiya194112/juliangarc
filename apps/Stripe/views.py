import stripe
import logging
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from django.db.models import Sum, Q
from datetime import date, timedelta
from django.http import JsonResponse
from django.http import HttpResponse
from django.utils.timezone import now
from apps.accounts.models import User
from apps.Stripe.models import Payout
from apps.Stripe.models import Payment
from apps.bookings.models import Booking
from rest_framework.response import Response
from stripe._error import SignatureVerificationError  
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from apps.subscriptions.models import SubscriptionPlan, Subscription
from apps.Stripe.serializers import PayoutSerializer, PaymentSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes


logger = logging.getLogger(__name__)


# 1. Host onboarding to Stripe
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
        


#Host will request for immediate payout/withdraw
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def host_withdraw_now(request):
    """Allow a host to request immediate payout of their completed paid bookings."""
    user = request.user

    if user.role != 'host':
        return Response({'error': 'Only hosts can request payouts.'}, status=status.HTTP_403_FORBIDDEN)

    # ✅ Step 2: Ensure Stripe account is linked
    if not user.stripe_account_id:
        return Response({'error': 'Stripe Connect account not linked. Please complete onboarding first.'},
                        status=status.HTTP_400_BAD_REQUEST)

    # ✅ Step 3: Get unpaid, completed bookings
    bookings = Booking.objects.filter(
        station__host=user,
        status='completed',
        is_paid=True,
        payouts__isnull=True  # not already included in any payout
    )

    if not bookings.exists():
        return Response({'error': 'No available balance to withdraw.'}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ Step 4: Calculate total
    total_amount = bookings.aggregate(total=Sum('subtotal'))['total'] or 0

    if total_amount <= 0:
        return Response({'error': 'No valid amount for payout.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # ✅ Step 5: Create Stripe Payout
        payout = stripe.Payout.create(
            amount=int(total_amount * 100),  # amount in cents
            currency='usd',
            stripe_account=user.stripe_account_id,
            metadata={
                'host_id': user.id,
                'booking_count': bookings.count(),
                'booking_ids': ','.join(str(b.id) for b in bookings)
            }
        )

        # ✅ Step 6: Record payout in DB
        payout_record = Payout.objects.create(
            host=user,
            amount=total_amount,
            stripe_payout_id=payout.id,
            stripe_account_id=user.stripe_account_id,
            status=payout.status or 'pending'
        )
        payout_record.bookings.set(bookings)
        payout_record.save()

        return Response({
            'message': 'Payout request submitted successfully.',
            'payout_id': payout_record.id,
            'amount': str(total_amount),
            'currency': 'USD',
            'status': payout_record.status,
            'expected_arrival_date': payout_record.expected_arrival_date
        }, status=status.HTTP_201_CREATED)

    except stripe.StripeError as e:
        return Response({'error': e.user_message or str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def host_earnings_and_payouts(request):
    """
    Get earnings overview, next payout, and transaction history for a host.
    """
    user = request.user

    if user.role != 'host':
        return Response({'error': 'Only hosts can access payout overview.'}, status=status.HTTP_403_FORBIDDEN)

    # Get all completed & paid bookings for this host
    completed_bookings = Booking.objects.filter(
        station__host=user,
        status='completed',
        is_paid=True
    )

    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    month_start = today.replace(day=1)

    # Earnings Overview
    today_earnings = completed_bookings.filter(payment_date=today).aggregate(Sum('subtotal'))['subtotal__sum'] or 0
    week_earnings = completed_bookings.filter(payment_date__gte=week_start).aggregate(Sum('subtotal'))['subtotal__sum'] or 0
    month_earnings = completed_bookings.filter(payment_date__gte=month_start).aggregate(Sum('subtotal'))['subtotal__sum'] or 0

    # Unpaid balance (not in any payout yet)
    unpaid_bookings = completed_bookings.filter(payouts__isnull=True)
    estimated_amount = unpaid_bookings.aggregate(Sum('subtotal'))['subtotal__sum'] or 0

    # Next payout (if any exists in DB)
    next_payout = Payout.objects.filter(
        host=user,
        status__in=['pending', 'in_transit']
    ).order_by('created_at').first()

    # Transaction History (past payouts)
    transactions = Payout.objects.filter(
        host=user
    ).order_by('-created_at')[:10]  # latest 10

    transaction_data = [
        {
            "date": p.arrival_date.strftime("%b %d, %Y") if p.arrival_date else p.created_at.strftime("%b %d, %Y"),
            "method": "Stripe",
            "status": p.status.capitalize(),
            "amount": f"${p.amount:.2f}"
        }
        for p in transactions
    ]

    # Prepare response
    response_data = {
        "earnings_overview": {
            "today": f"${today_earnings:.2f}",
            "this_week": f"${week_earnings:.2f}",
            "this_month": f"${month_earnings:.2f}",
        },
        "next_payout": {
            "scheduled_date": next_payout.expected_arrival_date.strftime("%b %d, %Y") if next_payout else None,
            "estimated_amount": f"${estimated_amount:.2f}",
        },
        "transaction_history": transaction_data
    }

    return Response(response_data, status=status.HTTP_200_OK)





@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def remove_stripe_account(request):
    """API to remove Stripe account for a specific user."""

    # Validate input (user_id)
    user_id = request.data.get('user_id')
    if not user_id:
        return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Fetch the user based on user_id
        user = User.objects.get(id=user_id)
        
        if not user.stripe_account_id:
            return Response({"error": "No Stripe account found for this user."}, status=status.HTTP_404_NOT_FOUND)

        # Delete the Stripe account
        try:
            stripe.Account.delete(user.stripe_account_id)
            logger.info(f"Successfully deleted Stripe account for user: {user.email}")

            # Clear the Stripe account ID and customer ID from the user profile
            user.stripe_account_id = None
            user.stripe_customer_id = None
            user.save()

            return Response({"message": "Stripe account removed successfully."}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            # If there is an error with the Stripe API
            logger.error(f"Error removing Stripe account for {user.email}: {e.user_message}")
            return Response({"error": e.user_message or "Stripe API error."}, status=status.HTTP_400_BAD_REQUEST)

    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




#Admin transfer the host's earnings
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




@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        return HttpResponse(status=400)
    except SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        return HttpResponse(status=400)

    # Handle the successful checkout session for payments
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Process payment success
        if 'booking_id' in session['metadata']:
            booking_id = session['metadata']['booking_id']
            try:
                booking = Booking.objects.get(id=booking_id)
                booking.is_paid = True
                booking.payment_date = timezone.now()
                booking.save(update_fields=["is_paid", "payment_date"])
                logger.info(f"Booking #{booking.id} payment successful.")
            except Booking.DoesNotExist:
                logger.error(f"Booking not found for ID: {booking_id}")
                return HttpResponse(status=404)
        
        # Process subscription (if relevant)
        elif 'user_id' in session['metadata'] and 'plan_id' in session['metadata']:
            user_id = session['metadata']['user_id']
            plan_id = session['metadata']['plan_id']
            stripe_subscription_id = session.get('subscription')

            try:
                user = User.objects.get(id=user_id)
                plan = SubscriptionPlan.objects.get(id=plan_id)
            except (User.DoesNotExist, SubscriptionPlan.DoesNotExist):
                logger.error("User or Subscription Plan not found")
                return JsonResponse({'error': 'User or Plan not found'}, status=400)

            # Create or update subscription
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

            logger.info(f"Subscription activated for user {user.email}, plan: {plan.name}")

        else:
            logger.error(f"Unexpected event data: {event['data']}")
            return HttpResponse(status=400)

    else:
        # Unhandled event type
        logger.error(f"Unhandled event type: {event['type']}")
        return HttpResponse(status=200)

    return HttpResponse(status=200)



def payment_success(request):
    return JsonResponse({"message": "Payment successful!"})

def payment_cancel(request):
    return JsonResponse({"message": "Payment cancelled."})





@api_view(['GET'])
def stripe_onboarding_refresh(request):
    return Response({"message": "Stripe onboarding session expired. Please try again."}, status=200)


@api_view(['GET'])
def stripe_onboarding_return(request):
    return Response({"message": "Stripe onboarding completed successfully!"}, status=200)
