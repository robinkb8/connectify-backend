from django.db import models
from django.conf import settings
from django.utils import timezone


class Payment(models.Model):
    """Payment transaction model for Razorpay integration"""
    
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('authorized', 'Authorized'),
        ('captured', 'Captured'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    
    amount = models.IntegerField()  # Amount in paise
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    
    receipt = models.CharField(max_length=100)
    notes = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Payment {self.razorpay_order_id} - {self.user.username} - ₹{self.amount/100}"


class Subscription(models.Model):
    """User subscription model for pro features"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    starts_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Subscription - {self.user.username} - {self.status}"
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status == 'active' and self.expires_at > timezone.now()
    
    def activate(self):
        """Activate subscription and upgrade user to pro"""
        self.status = 'active'
        self.save()
        self.user.upgrade_to_pro()
    
    def deactivate(self):
        """Deactivate subscription and downgrade user from pro"""
        self.status = 'expired'
        self.save()
        self.user.downgrade_from_pro()