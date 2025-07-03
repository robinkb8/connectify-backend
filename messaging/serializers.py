# messaging/serializers.py - COMPLETE MESSAGING API SERIALIZERS
from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Chat, Message, MessageStatus

User = get_user_model()


class ChatParticipantSerializer(serializers.ModelSerializer):
    """
    Serializer for chat participants (users in chat)
    """
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


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying messages
    """
    sender = ChatParticipantSerializer(read_only=True)
    time_since_sent = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()
    is_own_message = serializers.SerializerMethodField()
    delivery_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id',
            'content',
            'message_type',
            'attachment_url',
            'sender',
            'created_at',
            'updated_at',
            'time_since_sent',
            'is_edited',
            'is_deleted',
            'reply_to',
            'is_own_message',
            'delivery_status'
        ]
        read_only_fields = [
            'id',
            'sender',
            'created_at',
            'updated_at',
            'time_since_sent',
            'is_own_message',
            'delivery_status'
        ]
    
    def get_time_since_sent(self, obj):
        """Calculate human-readable time since message sent"""
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.total_seconds() < 60:  # Less than 1 minute
            return "just now"
        elif diff.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m"
        elif diff.total_seconds() < 86400:  # Less than 1 day
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h"
        else:  # Show days
            days = int(diff.total_seconds() / 86400)
            if days == 1:
                return "1 day"
            elif days < 7:
                return f"{days} days"
            else:
                return obj.created_at.strftime("%b %d")
    
    def get_attachment_url(self, obj):
        """Return full URL for message attachment"""
        if obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            return obj.attachment.url
        return None
    
    def get_is_own_message(self, obj):
        """Check if current user sent this message"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.sender.id == request.user.id
        return False
    
    def get_delivery_status(self, obj):
        """Get delivery status for current user (if they didn't send it)"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Only show delivery status for messages user didn't send
            if obj.sender.id != request.user.id:
                status_record = MessageStatus.objects.filter(
                    message=obj,
                    user=request.user
                ).first()
                if status_record:
                    return {
                        'status': status_record.status,
                        'delivered_at': status_record.delivered_at,
                        'read_at': status_record.read_at
                    }
        return None


class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new messages
    """
    
    class Meta:
        model = Message
        fields = ['content', 'message_type', 'attachment', 'reply_to']
        extra_kwargs = {
            'content': {'required': True},
            'message_type': {'required': False, 'default': 'text'},
            'attachment': {'required': False},
            'reply_to': {'required': False}
        }
    
    def validate_content(self, value):
        """Validate message content"""
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("Message content cannot be empty.")
        
        if len(value.strip()) > 1000:
            raise serializers.ValidationError("Message is too long. Maximum 1000 characters.")
        
        return value.strip()
    
    def validate(self, data):
        """Cross-field validation"""
        message_type = data.get('message_type', 'text')
        content = data.get('content', '')
        attachment = data.get('attachment')
        
        # For non-text messages, allow shorter content
        if message_type != 'text' and attachment:
            if not content:
                data['content'] = f"Sent a {message_type}"
        
        return data


class ChatSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying chats in chat list
    """
    participants = ChatParticipantSerializer(many=True, read_only=True)
    last_message = MessageSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = [
            'id',
            'chat_name',
            'is_group_chat',
            'participants',
            'other_participant',
            'display_name',
            'last_message',
            'last_activity',
            'created_at',
            'unread_count'
        ]
        read_only_fields = [
            'id',
            'participants',
            'other_participant',
            'display_name',
            'last_message',
            'last_activity',
            'created_at',
            'unread_count'
        ]
    
    def get_unread_count(self, obj):
        """Count unread messages for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Count messages where user has unread status
            unread_statuses = MessageStatus.objects.filter(
                message__chat=obj,
                user=request.user,
                status__in=['sent', 'delivered']  # Not read yet
            ).count()
            return unread_statuses
        return 0
    
    def get_other_participant(self, obj):
        """For direct messages, get the other participant"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and not obj.is_group_chat:
            other_user = obj.get_other_participant(request.user)
            if other_user:
                return ChatParticipantSerializer(other_user, context=self.context).data
        return None
    
    def get_display_name(self, obj):
        """Get display name for chat"""
        if obj.is_group_chat and obj.chat_name:
            return obj.chat_name
        elif not obj.is_group_chat:
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                other_user = obj.get_other_participant(request.user)
                if other_user:
                    return other_user.full_name or other_user.username
        
        # Fallback
        participants = obj.participants.all()
        if participants.count() > 0:
            names = [p.full_name or p.username for p in participants[:3]]
            if participants.count() > 3:
                names.append(f"and {participants.count() - 3} others")
            return ", ".join(names)
        
        return "Chat"


class ChatCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new chats
    """
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        help_text="List of user IDs to add to chat"
    )
    
    class Meta:
        model = Chat
        fields = ['chat_name', 'is_group_chat', 'participant_ids']
        extra_kwargs = {
            'chat_name': {'required': False},
            'is_group_chat': {'required': False, 'default': False}
        }
    
    def validate_participant_ids(self, value):
        """Validate participant IDs"""
        if not value or len(value) < 1:
            raise serializers.ValidationError("At least one participant is required.")
        
        if len(value) > 50:  # Reasonable limit for group chats
            raise serializers.ValidationError("Too many participants. Maximum 50 allowed.")
        
        # Check if all users exist
        existing_users = User.objects.filter(id__in=value).count()
        if existing_users != len(value):
            raise serializers.ValidationError("Some participant IDs are invalid.")
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        is_group_chat = data.get('is_group_chat', False)
        participant_ids = data.get('participant_ids', [])
        
        # For direct messages, only allow 1 other participant
        if not is_group_chat and len(participant_ids) != 1:
            raise serializers.ValidationError(
                "Direct messages must have exactly 1 other participant."
            )
        
        # For group chats, require at least 2 participants (plus creator = 3 total)
        if is_group_chat and len(participant_ids) < 2:
            raise serializers.ValidationError(
                "Group chats must have at least 2 other participants."
            )
        
        # Group chats should have a name
        if is_group_chat and not data.get('chat_name'):
            data['chat_name'] = "Group Chat"
        
        return data
    
    def create(self, validated_data):
        """Create chat with participants"""
        participant_ids = validated_data.pop('participant_ids')
        request = self.context.get('request')
        
        # Create chat
        chat = Chat.objects.create(**validated_data)
        
        # Add creator to chat
        if request and request.user.is_authenticated:
            chat.participants.add(request.user)
        
        # Add other participants
        participants = User.objects.filter(id__in=participant_ids)
        chat.participants.add(*participants)
        
        return chat


class ChatDetailSerializer(ChatSerializer):
    """
    Extended serializer for single chat view with recent messages
    """
    recent_messages = serializers.SerializerMethodField()
    
    class Meta(ChatSerializer.Meta):
        fields = ChatSerializer.Meta.fields + ['recent_messages']
    
    def get_recent_messages(self, obj):
        """Get last 20 messages for chat preview"""
        recent = obj.messages.filter(
            is_deleted=False
        ).order_by('-created_at')[:20]
        
        # Reverse to show oldest first
        recent = reversed(recent)
        
        return MessageSerializer(
            recent, 
            many=True, 
            context=self.context
        ).data