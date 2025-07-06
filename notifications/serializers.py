from rest_framework import serializers
from .models import Notification, NotificationSettings
from authentication.models import User
from django.utils import timezone


class NotificationSenderSerializer(serializers.ModelSerializer):
    """Nested serializer for notification sender information"""
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'avatar']
        read_only_fields = ['id', 'username', 'full_name', 'avatar']
    
    def get_avatar(self, obj):
        """Return avatar URL with fallback"""
        if hasattr(obj, 'profile') and obj.profile.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile.avatar.url)
            return obj.profile.avatar.url
        return None


class NotificationSerializer(serializers.ModelSerializer):
    """Main serializer for notifications"""
    sender = NotificationSenderSerializer(read_only=True)
    time_since_created = serializers.SerializerMethodField()
    content_object_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'sender',
            'content_object_data',
            'is_read',
            'read_at',
            'created_at',
            'time_since_created'
        ]
        read_only_fields = [
            'id',
            'notification_type',
            'title', 
            'message',
            'sender',
            'content_object_data',
            'created_at',
            'time_since_created'
        ]
    
    def get_time_since_created(self, obj):
        """Calculate human-readable time since notification"""
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.total_seconds() < 60:  # Less than 1 minute
            return "Just now"
        elif diff.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m"
        elif diff.total_seconds() < 86400:  # Less than 1 day
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h"
        else:  # Show days
            days = int(diff.total_seconds() / 86400)
            return f"{days}d"
    
    def get_content_object_data(self, obj):
        """Get related object data based on notification type"""
        if not obj.content_object:
            return None
        
        try:
            if obj.notification_type == 'like':
                # For likes, return post data
                post = obj.content_object
                return {
                    'type': 'post',
                    'id': post.id,
                    'content': post.content[:100] + '...' if len(post.content) > 100 else post.content,
                    'image_url': post.image.url if post.image else None
                }
            
            elif obj.notification_type == 'comment':
                # For comments, return comment and post data
                comment = obj.content_object
                return {
                    'type': 'comment',
                    'id': comment.id,
                    'content': comment.content,
                    'post': {
                        'id': comment.post.id,
                        'content': comment.post.content[:50] + '...' if len(comment.post.content) > 50 else comment.post.content
                    }
                }
            
            elif obj.notification_type == 'follow':
                # For follows, return follower data
                follow = obj.content_object
                return {
                    'type': 'follow',
                    'id': follow.id,
                    'follower_id': follow.follower.id,
                    'following_id': follow.following.id
                }
            
            elif obj.notification_type == 'message':
                # For messages, return basic message data
                message = obj.content_object
                return {
                    'type': 'message',
                    'id': str(message.id),
                    'chat_id': str(message.chat.id),
                    'preview': message.content[:50] + '...' if len(message.content) > 50 else message.content
                }
            
            else:
                return {
                    'type': 'unknown',
                    'id': obj.object_id
                }
                
        except Exception as e:
            # Return basic data if serialization fails
            return {
                'type': 'error',
                'id': obj.object_id,
                'error': 'Failed to load content'
            }


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating notification read status"""
    
    class Meta:
        model = Notification
        fields = ['is_read']
    
    def update(self, instance, validated_data):
        """Update notification and set read timestamp"""
        if validated_data.get('is_read') and not instance.is_read:
            instance.mark_as_read()
        return instance


class NotificationSettingsSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences"""
    
    class Meta:
        model = NotificationSettings
        fields = [
            'likes_enabled',
            'comments_enabled',
            'follows_enabled',
            'mentions_enabled',
            'messages_enabled',
            'email_notifications',
            'push_notifications'
        ]
    
    def validate(self, attrs):
        """Validate notification settings"""
        # At least one notification type should be enabled
        notification_types = [
            attrs.get('likes_enabled', True),
            attrs.get('comments_enabled', True),
            attrs.get('follows_enabled', True),
            attrs.get('mentions_enabled', True),
            attrs.get('messages_enabled', True)
        ]
        
        if not any(notification_types):
            raise serializers.ValidationError(
                "At least one notification type must be enabled."
            )
        
        return attrs


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    total_count = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    recent_count = serializers.IntegerField()
    types_breakdown = serializers.DictField()
    
    class Meta:
        fields = ['total_count', 'unread_count', 'recent_count', 'types_breakdown']