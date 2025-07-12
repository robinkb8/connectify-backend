from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone


class NotificationSettings(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings'
    )
    
    # Notification type preferences
    likes_enabled = models.BooleanField(default=True)
    comments_enabled = models.BooleanField(default=True)
    follows_enabled = models.BooleanField(default=True)
    mentions_enabled = models.BooleanField(default=True)
    messages_enabled = models.BooleanField(default=True)
    
    # Delivery preferences
    email_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_settings'
        verbose_name = 'Notification Settings'
        verbose_name_plural = 'Notification Settings'
    
    def __str__(self):
        return f"Notification settings for {self.user.username}"


class Notification(models.Model):
    """Real-time notifications for user activities"""
    
    NOTIFICATION_TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('mention', 'Mention'),
        ('message', 'Message'),
        ('system', 'System'),
    ]
    
    # Core notification data
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        null=True,
        blank=True
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(max_length=100)
    message = models.TextField(max_length=500)
    
    # Generic foreign key for related objects
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @property
    def sender_username(self):
        """Get sender username safely"""
        return self.sender.username if self.sender else 'System'
    
    @property
    def sender_avatar(self):
        """Get sender avatar URL safely"""
        if self.sender and hasattr(self.sender, 'profile') and self.sender.profile.avatar:
            return self.sender.profile.avatar.url
        return None


# Auto-create notification settings for new users
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_notification_settings(sender, instance, created, **kwargs):
    """Create notification settings when new user is created"""
    if created:
        NotificationSettings.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_notification_settings(sender, instance, **kwargs):
    """Save notification settings when user is saved"""
    if hasattr(instance, 'notification_settings'):
        instance.notification_settings.save()
    else:
        NotificationSettings.objects.get_or_create(user=instance)