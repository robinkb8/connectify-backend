# core/serializers.py - CLEAN VERSION WITHOUT STORIES
from rest_framework import serializers
from .models import Post, PostLike, Comment
from authentication.models import User
from django.utils import timezone

class AuthorSerializer(serializers.ModelSerializer):
    """
    Nested serializer for user information in posts
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


class PostSerializer(serializers.ModelSerializer):
    """
    Main serializer for posts in the feed
    """
    author = AuthorSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()
    time_since_posted = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id',
            'content',
            'image_url',
            'author',
            'total_likes',
            'total_comments',
            'total_shares',
            'is_liked',
            'created_at',
            'time_since_posted',
            'is_active'
        ]
        read_only_fields = [
            'id',
            'author',
            'total_likes',
            'total_comments',
            'total_shares',
            'is_liked',
            'created_at',
            'time_since_posted'
        ]
    
    def get_image_url(self, obj):
        """Return full URL for post image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_time_since_posted(self, obj):
        """Calculate human-readable time since posting"""
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m"
        elif diff.total_seconds() < 86400:  # Less than 1 day
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h"
        else:  # Show days
            days = int(diff.total_seconds() / 86400)
            return f"{days}d"
    
    def get_is_liked(self, obj):
        """Check if current user has liked this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(post=obj, user=request.user).exists()
        return False


class PostCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new posts
    """
    
    class Meta:
        model = Post
        fields = ['content', 'image']
        extra_kwargs = {
            'content': {'required': True},
            'image': {'required': False},
        }
    
    def validate_content(self, value):
        """Validate post content"""
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("Post content cannot be empty.")
        
        if len(value.strip()) > 2200:
            raise serializers.ValidationError("Post is too long. Maximum 2200 characters.")
        
        return value.strip()
    
class PostUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing posts
    Allows editing content and image
    """
    
    class Meta:
        model = Post
        fields = ['content', 'image']
        extra_kwargs = {
            'content': {'required': False},  # Allow partial updates
            'image': {'required': False},
        }
    
    def validate_content(self, value):
        """Validate post content"""
        if value is not None:  # Only validate if content is being updated
            if len(value.strip()) < 1:
                raise serializers.ValidationError("Post content cannot be empty.")
            
            if len(value.strip()) > 2200:
                raise serializers.ValidationError("Post is too long. Maximum 2200 characters.")
            
            return value.strip()
        return value
    
    def update(self, instance, validated_data):
        """Custom update method to handle image updates"""
        # Update content if provided
        if 'content' in validated_data:
            instance.content = validated_data['content']
        
        # Handle image update
        if 'image' in validated_data:
            # Delete old image if replacing with new one
            if instance.image and validated_data['image']:
                instance.image.delete(save=False)
            
            instance.image = validated_data['image']
        
        # Update the updated_at timestamp
        instance.updated_at = timezone.now()
        instance.save()
        
        return instance


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying comments
    """
    author = AuthorSerializer(read_only=True)
    time_since_posted = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id',
            'content',
            'author',
            'created_at',
            'time_since_posted',
            'parent_comment',
            'replies_count'
        ]
        read_only_fields = [
            'id',
            'author',
            'created_at',
            'time_since_posted',
            'replies_count'
        ]
    
    def get_time_since_posted(self, obj):
        """Calculate human-readable time since comment"""
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m"
        elif diff.total_seconds() < 86400:  # Less than 1 day
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h"
        else:  # Show days
            days = int(diff.total_seconds() / 86400)
            return f"{days}d"
    
    def get_replies_count(self, obj):
        """Count replies to this comment"""
        return obj.replies.count()


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new comments
    """
    
    class Meta:
        model = Comment
        fields = ['content', 'parent_comment']
        extra_kwargs = {
            'content': {'required': True},
            'parent_comment': {'required': False},
        }
    
    def validate_content(self, value):
        """Validate comment content"""
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("Comment cannot be empty.")
        
        if len(value.strip()) > 500:
            raise serializers.ValidationError("Comment is too long. Maximum 500 characters.")
        
        return value.strip()


class PostDetailSerializer(PostSerializer):
    """
    Extended serializer for single post view
    """
    comments = CommentSerializer(many=True, read_only=True)
    recent_comments = serializers.SerializerMethodField()
    
    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ['comments', 'recent_comments']
    
    def get_recent_comments(self, obj):
        """Get last 3 comments for preview"""
        recent = obj.comments.filter(parent_comment=None).order_by('-created_at')[:3]
        return CommentSerializer(recent, many=True, context=self.context).data