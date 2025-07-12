from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def get_subscription_duration():
    """Get subscription duration in days"""
    return 30  # 30 days for pro subscription


def calculate_subscription_end_date(start_date=None):
    """
    Calculate subscription end date
    
    Args:
        start_date: Start date for subscription (default: now)
        
    Returns:
        datetime: End date for subscription
    """
    if not start_date:
        start_date = timezone.now()
    
    duration_days = get_subscription_duration()
    end_date = start_date + timedelta(days=duration_days)
    
    return end_date


def get_pro_subscription_amount():
    """Get pro subscription amount in paise"""
    return settings.RAZORPAY_SETTINGS['SUBSCRIPTION_AMOUNT']  # ₹10 = 1000 paise


def format_amount_display(amount_paise):
    """
    Format amount for display
    
    Args:
        amount_paise: Amount in paise
        
    Returns:
        str: Formatted amount string
    """
    amount_rupees = amount_paise / 100
    return f"₹{amount_rupees:.2f}"


def create_payment_notes(user, subscription_type='pro'):
    """
    Create notes for payment
    
    Args:
        user: User object
        subscription_type: Type of subscription
        
    Returns:
        dict: Notes for payment
    """
    return {
        'user_id': str(user.id),
        'username': user.username,
        'email': user.email,
        'subscription_type': subscription_type,
        'platform': 'connectify'
    }


def validate_payment_amount(amount_paise):
    """
    Validate payment amount
    
    Args:
        amount_paise: Amount in paise
        
    Returns:
        tuple: (is_valid, error_message)
    """
    expected_amount = get_pro_subscription_amount()
    
    if amount_paise != expected_amount:
        return False, f"Invalid amount. Expected {format_amount_display(expected_amount)}"
    
    if amount_paise < 100:  # Minimum ₹1
        return False, "Amount too small"
    
    if amount_paise > 500000:  # Maximum ₹5000
        return False, "Amount too large"
    
    return True, None


def check_user_subscription_eligibility(user):
    """
    Check if user is eligible for new subscription
    
    Args:
        user: User object
        
    Returns:
        tuple: (is_eligible, message)
    """
    if user.is_pro:
        return False, "User already has an active pro subscription"
    
    # Check for any recent subscriptions
    from .models import Subscription
    recent_subscription = Subscription.objects.filter(
        user=user,
        status='active'
    ).first()
    
    if recent_subscription and recent_subscription.is_active:
        return False, "User has an active subscription"
    
    return True, "User is eligible for subscription"


def process_successful_payment(payment_obj):
    """
    Process successful payment and activate subscription
    
    Args:
        payment_obj: Payment model instance
        
    Returns:
        tuple: (success, subscription_obj, message)
    """
    try:
        from .models import Subscription
        
        # Check if subscription already exists
        existing_subscription = Subscription.objects.filter(
            payment=payment_obj
        ).first()
        
        if existing_subscription:
            return True, existing_subscription, "Subscription already processed"
        
        # Calculate subscription dates
        start_date = timezone.now()
        end_date = calculate_subscription_end_date(start_date)
        
        # Create subscription
        subscription = Subscription.objects.create(
            user=payment_obj.user,
            payment=payment_obj,
            starts_at=start_date,
            expires_at=end_date,
            status='active'
        )
        
        # Activate subscription (this will upgrade user to pro)
        subscription.activate()
        
        logger.info(f"Subscription activated for user {payment_obj.user.username}")
        
        return True, subscription, "Subscription activated successfully"
        
    except Exception as e:
        logger.error(f"Failed to process payment {payment_obj.id}: {str(e)}")
        return False, None, f"Failed to process payment: {str(e)}"


def cleanup_expired_subscriptions():
    """
    Cleanup expired subscriptions and downgrade users
    This function should be run periodically (e.g., daily cron job)
    """
    from .models import Subscription
    
    expired_subscriptions = Subscription.objects.filter(
        status='active',
        expires_at__lt=timezone.now()
    )
    
    count = 0
    for subscription in expired_subscriptions:
        try:
            subscription.deactivate()
            count += 1
            logger.info(f"Deactivated expired subscription for user {subscription.user.username}")
        except Exception as e:
            logger.error(f"Failed to deactivate subscription {subscription.id}: {str(e)}")
    
    logger.info(f"Cleaned up {count} expired subscriptions")
    return count


def get_user_payment_history(user, limit=10):
    """
    Get user's payment history
    
    Args:
        user: User object
        limit: Number of payments to return
        
    Returns:
        QuerySet: User's payments
    """
    from .models import Payment
    
    return Payment.objects.filter(
        user=user
    ).order_by('-created_at')[:limit]


def get_payment_success_data(payment_obj, subscription_obj):
    """
    Get payment success response data
    
    Args:
        payment_obj: Payment model instance
        subscription_obj: Subscription model instance
        
    Returns:
        dict: Success response data
    """
    return {
        'payment_id': payment_obj.razorpay_payment_id,
        'order_id': payment_obj.razorpay_order_id,
        'amount': format_amount_display(payment_obj.amount),
        'status': payment_obj.status,
        'subscription': {
            'id': subscription_obj.id,
            'status': subscription_obj.status,
            'starts_at': subscription_obj.starts_at.isoformat(),
            'expires_at': subscription_obj.expires_at.isoformat(),
        },
        'user_pro_status': payment_obj.user.is_pro,
        'message': f'Welcome to Connectify Pro! Your subscription is active until {subscription_obj.expires_at.strftime("%B %d, %Y")}'
    }