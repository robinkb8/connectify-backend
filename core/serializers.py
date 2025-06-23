# core/serializers.py
from rest_framework import serializers
from .models import Post, PostLike, Comment
from authentication.models import User

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
    🎓 LEARNING: Separate Serializer for Creation
    
    Sometimes you want different fields for creating vs viewing
    This serializer handles POST requests to create new posts
    """
    
    class Meta:
        model = Post
        fields = ['content', 'image']
    
    def validate_content(self, value):
        """
        🎓 LEARNING: Custom Validation
        
        Add custom validation rules for post content
        """
        if len(value.strip()) < 1:
            raise serializers.ValidationError("Post content cannot be empty.")
        
        if len(value) > 2200:
            raise serializers.ValidationError("Post content is too long (max 2200 characters).")
        
        return value.strip()
    
    def create(self, validated_data):
        """
        🎓 LEARNING: Custom Create Method
        
        Override create to automatically set the author
        from the authenticated user making the request
        """
        request = self.context.get('request')
        validated_data['author'] = request.user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    """
    🎓 LEARNING: Comments Serializer
    
    For future use when we add comments API
    Included here for completeness
    """
    author = AuthorSerializer(read_only=True)
    time_since_posted = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id',
            'content',
            'author', 
            'created_at',
            'time_since_posted',
            'parent_comment'
        ]
        read_only_fields = ['id', 'created_at', 'time_since_posted']
    
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
        else:
            return obj.created_at.strftime("%b %d")


class PostDetailSerializer(PostSerializer):
    """
    🎓 LEARNING: Extended Serializer for Detail Views
    
    When viewing a single post, we might want more information
    like comments, which we don't need in the list view
    """
    comments = CommentSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    
    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ['comments', 'comments_count']
    
    def get_comments_count(self, obj):
        """Get total number of comments for this post"""
        return obj.comments.count()


# 🎓 LEARNING: Serializer Usage Examples
"""
Example JSON Output from PostSerializer:

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
  "is_active": true
}

This JSON is exactly what your React PostCard component needs!
"""