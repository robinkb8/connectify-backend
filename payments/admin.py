from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Payment, Subscription
from .payment_utils import format_amount_display


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model"""
    
    list_display = [
        'razorpay_order_id', 'user_link', 'amount_display', 
        'status', 'currency', 'created_at'
    ]
    list_filter = ['status', 'currency', 'created_at']
    search_fields = [
        'user__username', 'user__email', 'razorpay_order_id', 
        'razorpay_payment_id', 'receipt'
    ]
    readonly_fields = [
        'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature',
        'amount_display', 'created_at', 'updated_at'
    ]
    list_per_page = 25
    ordering = ['-created_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'user', 'amount', 'amount_display', 'currency', 'status'
            )
        }),
        ('Razorpay Details', {
            'fields': (
                'razorpay_order_id', 'razorpay_payment_id', 
                'razorpay_signature', 'receipt'
            )
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_link(self, obj):
        """Create clickable link to user"""
        url = reverse('admin:authentication_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def amount_display(self, obj):
        """Display formatted amount"""
        return format_amount_display(obj.amount)
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def has_add_permission(self, request):
        """Disable manual payment creation"""
        return False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for Subscription model"""
    
    list_display = [
        'user_link', 'status_display', 'payment_link', 
        'starts_at', 'expires_at', 'is_active_display'
    ]
    list_filter = ['status', 'starts_at', 'expires_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'payment_amount_display', 'is_active', 'created_at', 'updated_at'
    ]
    list_per_page = 25
    ordering = ['-created_at']
    
    fieldsets = (
        ('Subscription Information', {
            'fields': (
                'user', 'payment', 'payment_amount_display', 'status'
            )
        }),
        ('Duration', {
            'fields': ('starts_at', 'expires_at', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_link(self, obj):
        """Create clickable link to user"""
        url = reverse('admin:authentication_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def payment_link(self, obj):
        """Create clickable link to payment"""
        url = reverse('admin:payments_payment_change', args=[obj.payment.pk])
        return format_html('<a href="{}">{}</a>', url, obj.payment.razorpay_order_id)
    payment_link.short_description = 'Payment'
    payment_link.admin_order_field = 'payment__razorpay_order_id'
    
    def status_display(self, obj):
        """Display colored status"""
        colors = {
            'active': 'green',
            'expired': 'red',
            'cancelled': 'orange'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    def is_active_display(self, obj):
        """Display active status with icon"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        else:
            return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active_display.short_description = 'Currently Active'
    
    def payment_amount_display(self, obj):
        """Display formatted payment amount"""
        return format_amount_display(obj.payment.amount)
    payment_amount_display.short_description = 'Payment Amount'
    
    def has_add_permission(self, request):
        """Disable manual subscription creation"""
        return False
    
    actions = ['activate_subscriptions', 'deactivate_subscriptions']
    
    def activate_subscriptions(self, request, queryset):
        """Activate selected subscriptions"""
        updated = 0
        for subscription in queryset:
            if subscription.status != 'active':
                subscription.activate()
                updated += 1
        
        self.message_user(request, f'{updated} subscriptions activated.')
    activate_subscriptions.short_description = 'Activate selected subscriptions'
    
    def deactivate_subscriptions(self, request, queryset):
        """Deactivate selected subscriptions"""
        updated = 0
        for subscription in queryset:
            if subscription.status == 'active':
                subscription.deactivate()
                updated += 1
        
        self.message_user(request, f'{updated} subscriptions deactivated.')
    deactivate_subscriptions.short_description = 'Deactivate selected subscriptions'