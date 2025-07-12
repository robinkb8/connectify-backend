import razorpay
from django.conf import settings
from django.utils import timezone
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)


class RazorpayClient:
    """Razorpay client wrapper for payment processing"""
    
    def __init__(self):
        self.client = razorpay.Client(auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ))
        self.currency = settings.RAZORPAY_SETTINGS['CURRENCY']
        self.receipt_prefix = settings.RAZORPAY_SETTINGS['RECEIPT_PREFIX']
    
    def create_order(self, amount, user_id, notes=None):
        """
        Create Razorpay order for payment
        
        Args:
            amount: Amount in rupees (will be converted to paise)
            user_id: User ID for receipt generation
            notes: Additional notes for the order
            
        Returns:
            dict: Razorpay order response
        """
        try:
            # Convert rupees to paise
            amount_paise = int(amount * 100)
            
            # Generate unique receipt
            receipt = f"{self.receipt_prefix}{user_id}_{int(timezone.now().timestamp())}"
            
            order_data = {
                'amount': amount_paise,
                'currency': self.currency,
                'receipt': receipt,
                'notes': notes or {}
            }
            
            order = self.client.order.create(data=order_data)
            
            logger.info(f"Razorpay order created: {order['id']} for user {user_id}")
            
            return {
                'success': True,
                'order': order
            }
            
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment_signature(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """
        Verify Razorpay payment signature for security
        
        Args:
            razorpay_order_id: Order ID from Razorpay
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Signature from Razorpay
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            # Create the signature verification string
            body = f"{razorpay_order_id}|{razorpay_payment_id}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                key=settings.RAZORPAY_KEY_SECRET.encode(),
                msg=body.encode(),
                digestmod=hashlib.sha256
            ).hexdigest()
            
            # Verify signature
            is_valid = hmac.compare_digest(expected_signature, razorpay_signature)
            
            if is_valid:
                logger.info(f"Payment signature verified for payment {razorpay_payment_id}")
            else:
                logger.warning(f"Invalid payment signature for payment {razorpay_payment_id}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Failed to verify payment signature: {str(e)}")
            return False
    
    def fetch_payment(self, payment_id):
        """
        Fetch payment details from Razorpay
        
        Args:
            payment_id: Razorpay payment ID
            
        Returns:
            dict: Payment details from Razorpay
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            
            logger.info(f"Fetched payment details: {payment_id}")
            
            return {
                'success': True,
                'payment': payment
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch payment {payment_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def fetch_order(self, order_id):
        """
        Fetch order details from Razorpay
        
        Args:
            order_id: Razorpay order ID
            
        Returns:
            dict: Order details from Razorpay
        """
        try:
            order = self.client.order.fetch(order_id)
            
            logger.info(f"Fetched order details: {order_id}")
            
            return {
                'success': True,
                'order': order
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch order {order_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def refund_payment(self, payment_id, amount=None, notes=None):
        """
        Refund a payment
        
        Args:
            payment_id: Razorpay payment ID to refund
            amount: Amount to refund in paise (None for full refund)
            notes: Additional notes for the refund
            
        Returns:
            dict: Refund response from Razorpay
        """
        try:
            refund_data = {}
            
            if amount:
                refund_data['amount'] = amount
            
            if notes:
                refund_data['notes'] = notes
            
            refund = self.client.payment.refund(payment_id, refund_data)
            
            logger.info(f"Payment refunded: {payment_id}")
            
            return {
                'success': True,
                'refund': refund
            }
            
        except Exception as e:
            logger.error(f"Failed to refund payment {payment_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Global client instance
razorpay_client = RazorpayClient()