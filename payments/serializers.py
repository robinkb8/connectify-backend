from rest_framework import serializers
from .models import Payment, Subscription
from .payment_utils import format_amount_display


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    
    amount_display = serializers.SerializerMethodField()
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_username', 'razorpay_order_id', 
            'razorpay_payment_id', 'amount', 'amount_display', 
            'currency', 'status', 'receipt', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_username', 'razorpay_order_id',
            'razorpay_payment_id', 'amount_display', 'created_at', 'updated_at'
        ]
    
    def get_amount_display(self, obj):
        """Get formatted amount for display"""
        return format_amount_display(obj.amount)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    payment_amount_display = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_username', 'payment', 'payment_amount_display',
            'status', 'is_active', 'starts_at', 'expires_at', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_username', 'payment_amount_display', 
            'is_active', 'created_at', 'updated_at'
        ]
    
    def get_payment_amount_display(self, obj):
        """Get formatted payment amount for display"""
        return format_amount_display(obj.payment.amount)


class CreateOrderSerializer(serializers.Serializer):
    """Serializer for creating Razorpay order"""
    
    amount = serializers.IntegerField(
        min_value=1000,  # Minimum ₹10
        max_value=500000,  # Maximum ₹5000
        help_text="Amount in paise (₹10 = 1000 paise)"
    )
    
    def validate_amount(self, value):
        """Validate amount for pro subscription"""
        from .payment_utils import validate_payment_amount
        
        is_valid, error_message = validate_payment_amount(value)
        if not is_valid:
            raise serializers.ValidationError(error_message)
        
        return value


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer for verifying Razorpay payment"""
    
    razorpay_order_id = serializers.CharField(max_length=100)
    razorpay_payment_id = serializers.CharField(max_length=100)
    razorpay_signature = serializers.CharField(max_length=200)
    
    def validate(self, data):
        """Validate payment verification data"""
        required_fields = ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature']
        
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"{field} is required")
        
        return data


class PaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for payment history"""
    
    amount_display = serializers.SerializerMethodField()
    subscription = SubscriptionSerializer(source='subscriptions.first', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'razorpay_order_id', 'razorpay_payment_id',
            'amount', 'amount_display', 'currency', 'status',
            'subscription', 'created_at'
        ]
        read_only_fields = fields
    
    def get_amount_display(self, obj):
        """Get formatted amount for display"""
        return format_amount_display(obj.amount)