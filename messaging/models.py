# messaging/models.py - COMPLETE MESSAGING MODELS
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinLengthValidator
import uuid


class Chat(models.Model):
    """
    Chat room between two or more users
    Supports both direct messages (2 users) and group chats (multiple users)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='chats',
        help_text="Users participating in this chat"
    )
    
    # Chat metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Chat settings
    is_group_chat = models.BooleanField(default=False)
    chat_name = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Optional name for group chats"
    )
    
    # Performance optimization
    last_message = models.ForeignKey(
        'Message',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_message_for_chat',
        help_text="Cache of the most recent message"
    )
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chats'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['-last_activity']),
            models.Index(fields=['is_group_chat']),
        ]
    
    def __str__(self):
        if self.is_group_chat and self.chat_name:
            return f"Group: {self.chat_name}"
        elif self.participants.count() == 2:
            users = list(self.participants.all()[:2])
            return f"Chat: {users[0].username} & {users[1].username}"
        else:
            return f"Chat {str(self.id)[:8]}..."
    
    def get_other_participant(self, user):
        """
        For direct messages, get the other participant
        """
        if not self.is_group_chat:
            return self.participants.exclude(id=user.id).first()
        return None
    
    def add_participant(self, user):
        """Add a user to the chat"""
        self.participants.add(user)
        self.save()
    
    def remove_participant(self, user):
        """Remove a user from the chat"""
        self.participants.remove(user)
        self.save()


class Message(models.Model):
    """
    Individual messages within a chat
    Supports text messages, images, and other file types
    """
    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System Message'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    
    # Message content
    content = models.TextField(
        validators=[MinLengthValidator(1)],
        help_text="Message text content"
    )
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPES,
        default='text'
    )
    
    # File attachments (optional)
    attachment = models.FileField(
        upload_to='messages/attachments/%Y/%m/%d/',
        blank=True,
        null=True,
        max_length=500
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Message status
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Reply functionality (optional)
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        if self.is_deleted:
            return f"[Deleted] Message by {self.sender.username}"
        return f"Message by {self.sender.username}: {self.content[:50]}..."
    
    def soft_delete(self):
        """Soft delete a message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def mark_as_edited(self):
        """Mark message as edited"""
        self.is_edited = True
        self.updated_at = timezone.now()
        self.save()


class MessageStatus(models.Model):
    """
    Track delivery and read status for each message per user
    Essential for read receipts and delivery confirmations
    """
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]
    
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='status_records'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_statuses'
    )
    
    # Status tracking
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='sent'
    )
    
    # Timestamps
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'message_statuses'
        unique_together = ['message', 'user']
        indexes = [
            models.Index(fields=['message', 'user']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.message.id}: {self.status}"
    
    def mark_delivered(self):
        """Mark message as delivered"""
        if self.status == 'sent':
            self.status = 'delivered'
            self.delivered_at = timezone.now()
            self.save()
    
    def mark_read(self):
        """Mark message as read"""
        if self.status in ['sent', 'delivered']:
            self.status = 'read'
            self.read_at = timezone.now()
            if not self.delivered_at:
                self.delivered_at = self.read_at
            self.save()


# Django Signals for automatic updates
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Message)
def update_chat_last_message(sender, instance, created, **kwargs):
    """Update chat's last_message when a new message is created"""
    if created and not instance.is_deleted:
        instance.chat.last_message = instance
        instance.chat.last_activity = timezone.now()
        instance.chat.save(update_fields=['last_message', 'last_activity'])

@receiver(post_save, sender=Message)
def create_message_status_records(sender, instance, created, **kwargs):
    """
    Automatically create MessageStatus records for all chat participants
    when a new message is created
    """
    if created:
        chat_participants = instance.chat.participants.exclude(id=instance.sender.id)
        
        # Create status records for all other participants
        status_records = [
            MessageStatus(
                message=instance,
                user=participant,
                status='sent'
            )
            for participant in chat_participants
        ]
        
        MessageStatus.objects.bulk_create(status_records)

@receiver(post_delete, sender=Message)
def update_chat_last_message_on_delete(sender, instance, **kwargs):
    """Update chat's last_message when the current last message is deleted"""
    if instance.chat.last_message and instance.chat.last_message.id == instance.id:
        # Find the new last message
        new_last_message = instance.chat.messages.filter(
            is_deleted=False
        ).exclude(id=instance.id).order_by('-created_at').first()
        
        instance.chat.last_message = new_last_message
        instance.chat.save(update_fields=['last_message'])