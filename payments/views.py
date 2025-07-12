from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
import logging

from .models import Payment, Subscription
from .serializers import (
    PaymentSerializer, SubscriptionSerializer, CreateOrderSerializer,
    VerifyPaymentSerializer, PaymentHistorySerializer
)
from .razorpay_client import razorpay_client
from .payment_utils import (
    get_pro_subscription_amount, create_payment_notes,
    check_user_subscription_eligibility, process_successful_payment,
    get_user_payment_history, get_payment_success_data
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """
    Create Razorpay order for pro subscription
    
    Args:
        request: POST request with amount in data
        
    Returns:
        Response with Razorpay order details
    """
    try:
        user = request.user
        
        # Check user eligibility
        is_eligible, message = check_user_subscription_eligibility(user)
        if not is_eligible:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate request data
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid request data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        amount_paise = serializer.validated_data['amount']
        amount_rupees = amount_paise / 100
        
        # Create payment notes
        notes = create_payment_notes(user)
        
        # Create Razorpay order
        order_response = razorpay_client.create_order(
            amount=amount_rupees,
            user_id=user.id,
            notes=notes
        )
        
        if not order_response['success']:
            return Response({
                'success': False,
                'message': 'Failed to create payment order',
                'error': order_response.get('error', 'Unknown error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        razorpay_order = order_response['order']
        
        # Create payment record in database
        payment = Payment.objects.create(
            user=user,
            razorpay_order_id=razorpay_order['id'],
            amount=amount_paise,
            currency=razorpay_order['currency'],
            receipt=razorpay_order['receipt'],
            notes=notes,
            status='created'
        )
        
        logger.info(f"Payment order created: {payment.razorpay_order_id} for user {user.username}")
        
        return Response({
            'success': True,
            'message': 'Order created successfully',
            'order': {
                'id': razorpay_order['id'],
                'amount': razorpay_order['amount'],
                'currency': razorpay_order['currency'],
                'receipt': razorpay_order['receipt'],
            },
            'payment_id': payment.id,
            'key_id': razorpay_client.client.auth[0]  # Frontend needs this for Razorpay
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Failed to create order for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """
    Verify Razorpay payment and activate subscription
    
    Args:
        request: POST request with Razorpay payment details
        
    Returns:
        Response with payment verification status and subscription details
    """
    try:
        user = request.user
        
        # Validate request data
        serializer = VerifyPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid verification data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        razorpay_order_id = serializer.validated_data['razorpay_order_id']
        razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
        razorpay_signature = serializer.validated_data['razorpay_signature']
        
        # Get payment record
        try:
            payment = Payment.objects.get(
                razorpay_order_id=razorpay_order_id,
                user=user
            )
        except Payment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Payment order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify payment signature
        is_valid_signature = razorpay_client.verify_payment_signature(
            razorpay_order_id, razorpay_payment_id, razorpay_signature
        )
        
        if not is_valid_signature:
            return Response({
                'success': False,
                'message': 'Invalid payment signature'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch payment details from Razorpay
        payment_response = razorpay_client.fetch_payment(razorpay_payment_id)
        if not payment_response['success']:
            return Response({
                'success': False,
                'message': 'Failed to verify payment with Razorpay',
                'error': payment_response.get('error', 'Unknown error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        razorpay_payment = payment_response['payment']
        
        # Update payment record with atomic transaction
        with transaction.atomic():
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = razorpay_payment['status']
            payment.save()
            
            # Process successful payment if captured
            if razorpay_payment['status'] == 'captured':
                success, subscription, message = process_successful_payment(payment)
                
                if not success:
                    return Response({
                        'success': False,
                        'message': message
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Get success response data
                success_data = get_payment_success_data(payment, subscription)
                
                logger.info(f"Payment verified and subscription activated for user {user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Payment verified and subscription activated successfully',
                    'data': success_data
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    'success': False,
                    'message': f'Payment not captured. Status: {razorpay_payment["status"]}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Failed to verify payment for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_status(request):
    """
    Get current user's subscription status
    
    Args:
        request: GET request from authenticated user
        
    Returns:
        Response with subscription status and details
    """
    try:
        user = request.user
        
        # Get user's active subscription
        try:
            subscription = Subscription.objects.get(
                user=user,
                status='active'
            )
            
            serializer = SubscriptionSerializer(subscription)
            
            return Response({
                'success': True,
                'has_subscription': True,
                'is_pro': user.is_pro,
                'subscription': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Subscription.DoesNotExist:
            return Response({
                'success': True,
                'has_subscription': False,
                'is_pro': user.is_pro,
                'subscription': None
            }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to get subscription status for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_history(request):
    """
    Get user's payment history
    
    Args:
        request: GET request with optional limit parameter
        
    Returns:
        Response with user's payment history
    """
    try:
        user = request.user
        limit = int(request.GET.get('limit', 10))
        limit = min(limit, 50)  # Maximum 50 payments
        
        payments = get_user_payment_history(user, limit)
        serializer = PaymentHistorySerializer(payments, many=True)
        
        return Response({
            'success': True,
            'payments': serializer.data,
            'total_payments': user.payments.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to get payment history for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscription_config(request):
    """
    Get subscription configuration details
    
    Args:
        request: GET request from authenticated user
        
    Returns:
        Response with subscription pricing and config
    """
    try:
        from .payment_utils import get_pro_subscription_amount, format_amount_display, get_subscription_duration
        
        amount_paise = get_pro_subscription_amount()
        
        return Response({
            'success': True,
            'config': {
                'amount_paise': amount_paise,
                'amount_display': format_amount_display(amount_paise),
                'currency': 'INR',
                'duration_days': get_subscription_duration(),
                'features': [
                    'Verified badge',
                    'Unlimited posts',
                    'Priority support',
                    'Advanced analytics',
                    'Custom themes',
                    'No advertisements'
                ]
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to get subscription config: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    """
    Cancel user's active subscription
    
    Args:
        request: POST request from authenticated user
        
    Returns:
        Response with cancellation status
    """
    try:
        user = request.user
        
        # Get user's active subscription
        try:
            subscription = Subscription.objects.get(
                user=user,
                status='active'
            )
            
            # Deactivate subscription
            subscription.deactivate()
            
            logger.info(f"Subscription cancelled for user {user.username}")
            
            return Response({
                'success': True,
                'message': 'Subscription cancelled successfully'
            }, status=status.HTTP_200_OK)
            
        except Subscription.DoesNotExist:
            return Response({
                'success': False,
                'message': 'No active subscription found'
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Failed to cancel subscription for user {request.user.username}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)