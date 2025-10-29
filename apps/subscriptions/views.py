import stripe
from datetime import timedelta
from rest_framework import status
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.subscriptions.utils import create_stripe_checkout_session
from apps.subscriptions.models import SubscriptionPlan, Subscription
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from apps.subscriptions.serializers import UserSubscriptionSerializer, SubscriptionPlanSerializer



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_subscription_plans(request):
    """Get all available subscription plans"""
    plans = SubscriptionPlan.objects.filter(
        plan_type__in=['basic', 'pro', 'business'],
        is_active=True
    )
    serializer = SubscriptionPlanSerializer(plans, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_subscriptions(request):
    """Get current user's subscriptions"""
    subscriptions = Subscription.objects.filter(user=request.user)
    serializer = UserSubscriptionSerializer(subscriptions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_subscription_payment(request):
    """Subscribe user to a plan using Stripe Checkout"""
    plan_id = request.data.get('plan_id')
    
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        return Response({'error': 'Subscription plan not found.'}, status=status.HTTP_404_NOT_FOUND)

    existing_subscription = Subscription.objects.filter(
        user=request.user, plan=plan
    ).first()

    if existing_subscription:
        existing_subscription.status = 'active'
        existing_subscription.start_date = timezone.now()
        existing_subscription.end_date = timezone.now() + timedelta(days=30)
        existing_subscription.save()

        return Response({
            'message': 'Subscription reactivated successfully',
            'subscription': UserSubscriptionSerializer(existing_subscription).data
        }, status=200)

    # For free plans — directly activate
    if plan.price == 0:
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30) if plan.billing_cycle == 'monthly' else timezone.now() + timedelta(days=365)
        )
        return Response(UserSubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)

    # For paid plans — create Stripe Checkout Session
    try:
        checkout_session = create_stripe_checkout_session(request.user, plan)

        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            stripe_subscription_id=None,  
            status='inactive',
            start_date=timezone.now(),
        )

        return Response({
            'checkout_url': checkout_session.url,  
            'subscription': UserSubscriptionSerializer(subscription).data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)