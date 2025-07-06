from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from .models import Notification, NotificationSettings


def create_notification(
    recipient,
    notification_type,
    title,
    message,
    sender=None,
    content_object=None
):
    """
    Generic notification creator
    
    Args:
        recipient: User who will receive the notification
        notification_type: Type of notification (like, comment, follow, etc.)
        title: Notification title
        message: Notification message
        sender: User who triggered the notification (optional)
        content_object: Related object (Post, Comment, etc.) (optional)
    """
    try:
        # Check if recipient has notifications enabled for this type
        settings_obj, created = NotificationSettings.objects.get_or_create(
            user=recipient
        )
        
        # Check notification preferences
        if not _should_send_notification(settings_obj, notification_type):
            return None
        
        # Don't send notifications to yourself
        if sender and sender == recipient:
            return None
        
        # Create notification
        notification_data = {
            'recipient': recipient,
            'sender': sender,
            'notification_type': notification_type,
            'title': title,
            'message': message,
        }
        
        # Add content object if provided
        if content_object:
            notification_data['content_type'] = ContentType.objects.get_for_model(content_object)
            notification_data['object_id'] = content_object.pk
        
        notification = Notification.objects.create(**notification_data)
        
        # TODO: Send real-time notification via WebSocket
        _send_realtime_notification(notification)
        
        return notification
        
    except Exception as e:
        # Log error but don't crash the main operation
        print(f"Error creating notification: {e}")
        return None


def create_like_notification(post_like):
    """Create notification for post like"""
    post = post_like.post
    liker = post_like.user
    post_author = post.author
    
    return create_notification(
        recipient=post_author,
        sender=liker,
        notification_type='like',
        title='New Like',
        message=f'{liker.username} liked your post',
        content_object=post
    )


def create_comment_notification(comment):
    """Create notification for new comment"""
    post = comment.post
    commenter = comment.author
    post_author = post.author
    
    # Create notification for post author
    notification = create_notification(
        recipient=post_author,
        sender=commenter,
        notification_type='comment',
        title='New Comment',
        message=f'{commenter.username} commented on your post',
        content_object=comment
    )
    
    # TODO: Create notifications for mentioned users in comment
    _create_mention_notifications(comment)
    
    return notification


def create_follow_notification(follow):
    """Create notification for new follower"""
    follower = follow.follower
    following = follow.following
    
    return create_notification(
        recipient=following,
        sender=follower,
        notification_type='follow',
        title='New Follower',
        message=f'{follower.username} started following you',
        content_object=follow
    )


def create_message_notification(message):
    """Create notification for new message"""
    sender = message.sender
    chat = message.chat
    
    # Get other participants in the chat
    for participant in chat.participants.exclude(id=sender.id):
        create_notification(
            recipient=participant,
            sender=sender,
            notification_type='message',
            title='New Message',
            message=f'{sender.username} sent you a message',
            content_object=message
        )


def mark_notifications_read(user, notification_type=None, content_object=None):
    """Mark notifications as read"""
    queryset = Notification.objects.filter(
        recipient=user,
        is_read=False
    )
    
    if notification_type:
        queryset = queryset.filter(notification_type=notification_type)
    
    if content_object:
        content_type = ContentType.objects.get_for_model(content_object)
        queryset = queryset.filter(
            content_type=content_type,
            object_id=content_object.pk
        )
    
    # Bulk update
    updated_count = queryset.update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return updated_count


def get_unread_count(user):
    """Get unread notification count for user"""
    return Notification.objects.filter(
        recipient=user,
        is_read=False
    ).count()


def _should_send_notification(settings_obj, notification_type):
    """Check if notification should be sent based on user preferences"""
    preference_map = {
        'like': settings_obj.likes_enabled,
        'comment': settings_obj.comments_enabled,
        'follow': settings_obj.follows_enabled,
        'mention': settings_obj.mentions_enabled,
        'message': settings_obj.messages_enabled,
        'system': True,  # System notifications are always sent
    }
    
    return preference_map.get(notification_type, True)


def _create_mention_notifications(comment):
    """Create notifications for mentioned users in comment"""
    import re
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Find @mentions in comment content
    mentions = re.findall(r'@(\w+)', comment.content)
    
    for username in mentions:
        try:
            mentioned_user = User.objects.get(username=username)
            create_notification(
                recipient=mentioned_user,
                sender=comment.author,
                notification_type='mention',
                title='You were mentioned',
                message=f'{comment.author.username} mentioned you in a comment',
                content_object=comment
            )
        except User.DoesNotExist:
            continue


def _send_realtime_notification(notification):
    """Send real-time notification via WebSocket"""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from .serializers import NotificationSerializer
        
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        # Create a mock request for serializer context
        class MockRequest:
            def __init__(self):
                self.user = notification.recipient
            
            def build_absolute_uri(self, url):
                return url
        
        # Serialize notification
        mock_request = MockRequest()
        serializer = NotificationSerializer(
            notification, 
            context={'request': mock_request}
        )
        
        # Send to user's notification group
        group_name = f'notifications_{notification.recipient.id}'
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'notification_created',
                'notification_data': serializer.data
            }
        )
        
        # Also send updated unread count
        unread_count = get_unread_count(notification.recipient)
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'unread_count_updated',
                'count': unread_count
            }
        )
        
    except Exception as e:
        # Don't crash if WebSocket fails
        print(f"Failed to send real-time notification: {e}")
        pass