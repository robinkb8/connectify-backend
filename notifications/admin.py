from django.contrib import admin
from .models import Notification, NotificationSettings


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for notifications"""
    list_display = [
        'id', 
        'recipient_username', 
        'sender_username', 
        'notification_type', 
        'title', 
        'is_read', 
        'created_at'
    ]
    list_filter = [
        'notification_type', 
        'is_read', 
        'created_at'
    ]
    search_fields = [
        'recipient__username', 
        'sender__username', 
        'title', 
        'message'
    ]
    readonly_fields = [
        'created_at', 
        'read_at'
    ]
    ordering = ['-created_at']
    
    def recipient_username(self, obj):
        return obj.recipient.username
    recipient_username.short_description = 'Recipient'
    
    def sender_username(self, obj):
        return obj.sender.username if obj.sender else 'System'
    sender_username.short_description = 'Sender'


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    """Admin interface for notification settings"""
    list_display = [
        'user_username',
        'likes_enabled',
        'comments_enabled', 
        'follows_enabled',
        'messages_enabled',
        'email_notifications'
    ]
    list_filter = [
        'likes_enabled',
        'comments_enabled',
        'follows_enabled', 
        'email_notifications'
    ]
    search_fields = ['user__username']
    
    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'User'