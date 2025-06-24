# core/serializers.py - UPDATED WITH COMMENT CREATION
from rest_framework import serializers
from .models import Post, PostLike, Comment, Story, StoryView 
from authentication.models import User



class StorySerializer(serializers.ModelSerializer):
    """
    Serializer for displaying stories in the stories section
    """
    author = AuthorSerializer(read_only=True)
    time_since_posted = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    is_viewed = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = [
            'id',
            'image_url',
            'caption',
            'author',
            'created_at',
            'expires_at',
            'total_views',
            'time_since_posted',
            'is_viewed',
            'is_expired'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'expires_at',
            'total_views',
            'time_since_posted',
            'is_viewed',
            'is_expired'
        ]
    
    def get_image_url(self, obj):
        """Return full URL for story image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_time_since_posted(self, obj):
        """Calculate human-readable time since story creation"""
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m"
        else:  # Show hours
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h"
    
    def get_is_viewed(self, obj):
        """Check if current user has viewed this story"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StoryView.objects.filter(
                story=obj,
                viewer=request.user
            ).exists()
        return False
    
    def get_is_expired(self, obj):
        """Check if story has expired (24 hours)"""
        return timezone.now() > obj.expires_at


class StoryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new stories
    """
    
    class Meta:
        model = Story
        fields = ['image', 'caption']
        extra_kwargs = {
            'image': {'required': True},
            'caption': {'required': False, 'allow_blank': True},
        }
    
    def validate_image(self, value):
        """Validate story image"""
        if not value:
            raise serializers.ValidationError("Story image is required.")
        
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Image size cannot exceed 10MB.")
        
        # Check file type
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        import os
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_extensions:
            raise serializers.ValidationError("Only JPG, PNG, and GIF images are allowed.")
        
        return value
    
    def create(self, validated_data):
        """Create story with automatic expiration time"""
        from datetime import timedelta
        
        # Set expiration to 24 hours from now
        validated_data['expires_at'] = timezone.now() + timedelta(hours=24)
        
        story = super().create(validated_data)
        print(f"✅ Story created with ID: {story.id}, expires at: {story.expires_at}")
        return story


class StoryDetailSerializer(StorySerializer):
    """
    Extended serializer for story detail view (when viewing a story)
    """
    viewers = serializers.SerializerMethodField()
    
    class Meta(StorySerializer.Meta):
        fields = StorySerializer.Meta.fields + ['viewers']
    
    def get_viewers(self, obj):
        """Get list of users who viewed this story"""
        views = StoryView.objects.filter(story=obj).select_related('viewer').order_by('-viewed_at')[:10]
        return [
            {
                'username': view.viewer.username,
                'avatar': AuthorSerializer(view.viewer, context=self.context).data.get('avatar'),
                'viewed_at': view.viewed_at
            }
            for view in views
        ]

class AuthorSerializer(serializers.ModelSerializer):
    """
    🎓 LEARNING: Nested Serializer
    
    This serializer handles user information that we want to include
    with each post (author details like username, avatar)
    """
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'avatar']
    
    def get_avatar(self, obj):
        """
        🎓 LEARNING: SerializerMethodField
        
        Custom field that calculates avatar URL
        If user has profile with avatar, return URL, otherwise return placeholder
        """
        try:
            if obj.profile.avatar:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.profile.avatar.url)
                return obj.profile.avatar.url
        except:
            pass
        return None


class PostSerializer(serializers.ModelSerializer):
    """
    🎓 LEARNING: Main Post Serializer
    
    This converts Post model to JSON format for API responses
    It includes nested author info and calculated fields
    """
    
    # Nested serializer for author information
    author = AuthorSerializer(read_only=True)
    
    # SerializerMethodFields for dynamic data
    is_liked = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    time_since_posted = serializers.SerializerMethodField()
    
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
            'total_likes', 
            'total_comments', 
            'total_shares', 
            'created_at',
            'is_liked',
            'time_since_posted'
        ]
    
    def get_is_liked(self, obj):
        """
        🎓 LEARNING: User-specific Data
        
        Check if the current authenticated user has liked this post
        This is how we show filled/empty hearts in React
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(
                user=request.user, 
                post=obj
            ).exists()
        return False
    
    def get_image_url(self, obj):
        """
        🎓 LEARNING: File URL Handling
        
        Return full URL for post images
        Handles cases where no image is uploaded
        """
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_time_since_posted(self, obj):
        """
        🎓 LEARNING: Time Calculation
        
        Calculate human-readable time since post creation
        Returns strings like "2h ago", "1d ago", etc.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days}d ago"
        else:
            return obj.created_at.strftime("%b %d")

class PostCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating posts with image upload
    """
    
    class Meta:
        model = Post
        fields = ['content', 'image']
        extra_kwargs = {
            'content': {'required': False, 'allow_blank': True},
            'image': {'required': False, 'allow_null': True},
        }
    
    def validate(self, data):
        """Ensure either content or image is provided"""
        content = data.get('content', '').strip()
        image = data.get('image')
        
        if not content and not image:
            raise serializers.ValidationError("Please provide either content or an image.")
        
        print(f"🔍 Validating data: content='{content}', image={image}")
        return data
    
    def create(self, validated_data):
        """Create post with proper logging"""
        print(f"🔍 Creating post with: {validated_data}")
        post = super().create(validated_data)
        print(f"✅ Post created with ID: {post.id}")
        return post


# ✅ UPDATED COMMENT SERIALIZERS
class CommentSerializer(serializers.ModelSerializer):
    """
    🎓 LEARNING: Comments Display Serializer
    
    For displaying comments in post detail view
    Includes author info and time calculation
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
        read_only_fields = ['id', 'created_at', 'time_since_posted', 'replies_count']
    
    def get_time_since_posted(self, obj):
        """Same time calculation as posts"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days}d ago"
        else:
            return obj.created_at.strftime("%b %d")
    
    def get_replies_count(self, obj):
        """Count how many replies this comment has"""
        return obj.replies.count()


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    ✅ NEW: Serializer for creating comments
    
    Simple serializer for posting new comments
    Only requires content, post and author set in view
    """
    
    class Meta:
        model = Comment
        fields = ['content', 'parent_comment']
        extra_kwargs = {
            'content': {'required': True, 'allow_blank': False},
            'parent_comment': {'required': False, 'allow_null': True},
        }
    
    def validate_content(self, value):
        """Validate comment content"""
        if not value or not value.strip():
            raise serializers.ValidationError("Comment cannot be empty.")
        
        if len(value.strip()) > 500:
            raise serializers.ValidationError("Comment is too long. Maximum 500 characters.")
        
        return value.strip()
    
    def validate_parent_comment(self, value):
        """Validate parent comment for replies"""
        if value:
            # Check if parent comment exists and belongs to same post
            # This will be validated in the view when we have the post context
            pass
        return value


class PostDetailSerializer(PostSerializer):
    """
    🎓 LEARNING: Extended Serializer for Detail Views
    
    When viewing a single post, we might want more information
    like comments, which we don't need in the list view
    """
    comments = CommentSerializer(many=True, read_only=True)
    recent_comments = serializers.SerializerMethodField()
    
    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ['comments', 'recent_comments']
    
    def get_recent_comments(self, obj):
        """Get last 3 comments for preview in feed"""
        recent = obj.comments.filter(parent_comment=None).order_by('-created_at')[:3]
        return CommentSerializer(recent, many=True, context=self.context).data


# 🎓 LEARNING: Serializer Usage Examples
"""
Example JSON Output from PostSerializer with Comments:

{
  "id": 1,
  "content": "Amazing sunset over the mountains!",
  "image_url": "http://127.0.0.1:8000/media/posts/images/2024/01/15/sunset.jpg",
  "author": {
    "id": 2,
    "username": "alex_photographer",
    "full_name": "Alex Johnson", 
    "avatar": "http://127.0.0.1:8000/media/avatars/alex.jpg"
  },
  "total_likes": 1247,
  "total_comments": 89,
  "total_shares": 34,
  "is_liked": false,
  "created_at": "2024-01-15T18:30:00Z",
  "time_since_posted": "2h ago",
  "is_active": true,
  "recent_comments": [
    {
      "id": 45,
      "content": "Absolutely stunning! 📸",
      "author": {
        "id": 5,
        "username": "nature_lover",
        "full_name": "Sarah Chen",
        "avatar": null
      },
      "time_since_posted": "30m ago",
      "replies_count": 2
    }
  ]
}

This JSON structure matches Instagram's feed perfectly!
"""