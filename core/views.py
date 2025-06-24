# core/views.py - UPDATED WITH COMMENT API ENDPOINTS
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Q

# ✅ ADD THESE MISSING IMPORTS
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Post, PostLike, Comment,Story, StoryView  # ✅ ADD Comment import
from .serializers import (
    PostSerializer, 
    PostCreateSerializer, 
    PostDetailSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    StorySerializer,          # Add these Story serializers
    StoryCreateSerializer,
    StoryDetailSerializer # ✅ ADD CommentCreateSerializer import
)

from django.utils import timezone
from datetime import timedelta

# ✅ NEW: STORIES API ENDPOINTS

class StoriesListAPIView(generics.ListAPIView):
    """
    🎓 LEARNING: Stories List API View
    
    Handles: GET /api/stories/
    Purpose: Return active stories for the stories section
    Features: Only non-expired stories, ordered by creation time
    """
    
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Get active (non-expired) stories"""
        now = timezone.now()
        
        # Get stories that haven't expired yet
        queryset = Story.objects.filter(
            expires_at__gt=now  # Only stories that haven't expired
        ).select_related(
            'author',
            'author__profile'
        ).prefetch_related(
            'views'
        ).order_by('-created_at')  # Newest first
        
        print(f"🔍 Found {queryset.count()} active stories")
        return queryset


class StoryCreateAPIView(generics.CreateAPIView):
    """
    🎓 LEARNING: Story Creation API View
    
    Handles: POST /api/stories/create/
    Purpose: Create new story with image upload
    Features: Automatic 24-hour expiration, image validation
    """
    
    serializer_class = StoryCreateSerializer
    permission_classes = [permissions.AllowAny]  # TODO: Change to IsAuthenticated
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        """Set author and expiration when creating story"""
        from authentication.models import User
        
        # TODO: Use request.user when authentication is implemented
        # For now, use existing user
        user = User.objects.filter(username='athul_user').first()
        if not user:
            user = User.objects.first()
        
        if not user:
            user = User.objects.create_user(
                email='test@test.com',
                username='testuser',
                full_name='Test User',
                phone='1234567890',
                password='test123'
            )
        
        story = serializer.save(author=user)
        print(f"✅ Story created by {user.username} with ID: {story.id}")


class StoryDetailAPIView(generics.RetrieveAPIView):
    """
    🎓 LEARNING: Story Detail API View
    
    Handles: GET /api/stories/1/
    Purpose: Get single story with details and viewers
    Features: Detailed story info for story viewer
    """
    
    serializer_class = StoryDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Get story with optimized queries"""
        return Story.objects.select_related(
            'author',
            'author__profile'
        ).prefetch_related(
            'views__viewer',
            'views__viewer__profile'
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to automatically mark story as viewed"""
        story = self.get_object()
        
        # TODO: Use request.user when authentication is implemented
        # For now, simulate viewing
        from authentication.models import User
        user = User.objects.filter(username='athul_user').first()
        
        if user and not story.expires_at < timezone.now():
            # Mark story as viewed (create view record if not exists)
            view, created = StoryView.objects.get_or_create(
                story=story,
                viewer=user
            )
            
            if created:
                # Update total views count
                story.total_views = story.views.count()
                story.save(update_fields=['total_views'])
                print(f"✅ Story {story.id} viewed by {user.username}")
        
        return super().retrieve(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def user_stories(request, user_id):
    """
    🎓 LEARNING: User Stories API Endpoint
    
    Handles: GET /api/users/1/stories/
    Purpose: Get all active stories by a specific user
    Features: Used for viewing all stories from one user
    """
    
    now = timezone.now()
    
    # Get user's active stories
    stories = Story.objects.filter(
        author_id=user_id,
        expires_at__gt=now
    ).select_related(
        'author',
        'author__profile'
    ).order_by('created_at')  # Oldest first for viewing
    
    serializer = StorySerializer(stories, many=True, context={'request': request})
    
    return Response({
        'user_id': user_id,
        'stories_count': stories.count(),
        'stories': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # TODO: Change to IsAuthenticated
def mark_story_viewed(request, story_id):
    """
    🎓 LEARNING: Mark Story as Viewed
    
    Handles: POST /api/stories/1/view/
    Purpose: Mark a story as viewed by current user
    Features: Tracking story views for analytics
    """
    
    story = get_object_or_404(Story, id=story_id)
    
    # Check if story has expired
    if story.expires_at < timezone.now():
        return Response({
            'success': False,
            'message': 'Story has expired'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # TODO: Use request.user when authentication is implemented
    from authentication.models import User
    user = User.objects.filter(username='athul_user').first()
    if not user:
        user = User.objects.first()
    
    if not user:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create or get view record
    view, created = StoryView.objects.get_or_create(
        story=story,
        viewer=user
    )
    
    if created:
        # Update total views count
        story.total_views = story.views.count()
        story.save(update_fields=['total_views'])
    
    return Response({
        'success': True,
        'message': 'Story marked as viewed' if created else 'Story already viewed',
        'total_views': story.total_views,
        'story_id': story.id
    })


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def stories_stats(request, story_id):
    """
    🎓 LEARNING: Story Statistics
    
    Handles: GET /api/stories/1/stats/
    Purpose: Get detailed statistics for a story
    Features: View count, recent viewers, engagement metrics
    """
    
    story = get_object_or_404(Story, id=story_id)
    
    # Get recent viewers
    recent_views = StoryView.objects.filter(story=story).select_related(
        'viewer'
    ).order_by('-viewed_at')[:10]
    
    recent_viewers = [
        {
            'username': view.viewer.username,
            'full_name': view.viewer.full_name,
            'viewed_at': view.viewed_at
        }
        for view in recent_views
    ]
    
    return Response({
        'story_id': story.id,
        'total_views': story.total_views,
        'recent_viewers': recent_viewers,
        'created_at': story.created_at,
        'expires_at': story.expires_at,
        'is_expired': timezone.now() > story.expires_at,
        'author': {
            'username': story.author.username,
            'full_name': story.author.full_name
        }
    })

# 🎓 LEARNING: Generic API Views
"""
Django REST Framework provides several generic views:
- ListAPIView: GET /api/posts/ (list all posts)
- CreateAPIView: POST /api/posts/ (create new post) 
- RetrieveAPIView: GET /api/posts/1/ (get single post)
- ListCreateAPIView: Combines list + create
- RetrieveUpdateDestroyAPIView: get + update + delete single item
"""

class PostListAPIView(generics.ListAPIView):
    """
    🎓 LEARNING: List API View
    
    Handles: GET /api/posts/
    Purpose: Return list of posts for the home feed
    Features: Pagination, filtering, ordering
    
    This is what your React HomeFeed component will call
    to get posts instead of using dummy data
    """
    
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # Anyone can read, must be logged in to write
    
    def get_queryset(self):
        """
        🎓 LEARNING: Dynamic QuerySet
        
        Customize which posts to return based on request parameters
        Includes optimizations for better performance
        """
        queryset = Post.objects.filter(is_active=True).select_related(
            'author',           # Optimize: Load author info in same query
            'author__profile'   # Optimize: Load author profile for avatar
        ).prefetch_related(
            'likes',           # Optimize: Reduce database queries for likes
            'comments'         # Optimize: Reduce database queries for comments
        ).order_by('-created_at')  # Newest first (Instagram-style)
        
        # 🎯 Optional: Add filtering by author (for user profiles)
        author_id = self.request.query_params.get('author', None)
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        # 🎯 Optional: Add search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(content__icontains=search) | 
                Q(author__username__icontains=search)
            )
        
        return queryset

@method_decorator(csrf_exempt, name='dispatch')
class PostCreateAPIView(generics.CreateAPIView):
    """
    Handle POST /api/posts/create/ with file uploads
    """
    
    serializer_class = PostCreateSerializer
    permission_classes = [permissions.AllowAny]  # TODO: Change to IsAuthenticated in production
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def perform_create(self, serializer):
        """Set author automatically"""
        from authentication.models import User
        
        # TODO: Use request.user when authentication is implemented
        # For now, use existing user or create test user
        user = User.objects.filter(username='athul_user').first()
        if not user:
            user = User.objects.first()
        
        if not user:
            user = User.objects.create_user(
                email='test@test.com',
                username='testuser',
                full_name='Test User',
                phone='1234567890',
                password='test123'
            )
        
        post = serializer.save(author=user)
        print(f"✅ Post created by {user.username} with ID: {post.id}")
        if post.image:
            print(f"✅ Image saved: {post.image.url}")
    
    def create(self, request, *args, **kwargs):
        """Add debugging for image uploads"""
        print(f"🔍 POST request for image upload")
        print(f"🔍 Content-Type: {request.content_type}")
        print(f"🔍 Files received: {list(request.FILES.keys())}")
        print(f"🔍 Data received: {list(request.data.keys())}")
        
        if 'image' in request.FILES:
            image = request.FILES['image']
            print(f"🔍 Image details: name={image.name}, size={image.size}, type={image.content_type}")
        
        try:
            response = super().create(request, *args, **kwargs)
            print(f"✅ Response created successfully")
            return response
        except Exception as e:
            print(f"❌ Error in create: {e}")
            import traceback
            traceback.print_exc()
            raise e

class PostDetailAPIView(generics.RetrieveAPIView):
    """
    🎓 LEARNING: Retrieve API View
    
    Handles: GET /api/posts/1/
    Purpose: Get single post with full details (including comments)
    Features: Detailed post info for post detail pages
    """
    
    queryset = Post.objects.filter(is_active=True)
    serializer_class = PostDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Optimize database queries for single post view"""
        return super().get_queryset().select_related(
            'author',
            'author__profile'
        ).prefetch_related(
            'likes',
            'comments__author',
            'comments__author__profile'
        )


# ✅ NEW: COMMENT API ENDPOINTS
class PostCommentsListCreateAPIView(generics.ListCreateAPIView):
    """
    🎓 LEARNING: List + Create API View for Comments
    
    Handles: GET /api/posts/1/comments/ - List all comments for a post
             POST /api/posts/1/comments/ - Create new comment on a post
    """
    
    permission_classes = [permissions.AllowAny]  # TODO: Change to IsAuthenticated for POST
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer
    
    def get_queryset(self):
        """Get comments for specific post"""
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(
            post_id=post_id
        ).select_related(
            'author',
            'author__profile'
        ).order_by('created_at')  # Oldest first (Instagram-style)
    
    def perform_create(self, serializer):
        """Set post and author when creating comment"""
        from authentication.models import User
        
        # Get the post
        post_id = self.kwargs['post_id']
        post = get_object_or_404(Post, id=post_id, is_active=True)
        
        # TODO: Use request.user when authentication is implemented
        # For now, use existing user
        user = User.objects.filter(username='athul_user').first()
        if not user:
            user = User.objects.first()
        
        comment = serializer.save(post=post, author=user)
        print(f"✅ Comment created by {user.username} on post {post.id}")


class CommentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    🎓 LEARNING: Full CRUD for individual comments
    
    Handles: GET /api/comments/1/ - Get specific comment
             PUT /api/comments/1/ - Update comment (only by author)
             DELETE /api/comments/1/ - Delete comment (only by author)
    """
    
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.AllowAny]  # TODO: Add proper permissions
    
    def get_queryset(self):
        """Optimize database queries"""
        return super().get_queryset().select_related(
            'author',
            'author__profile',
            'post'
        )


# 🎓 LEARNING: Function-Based API Views (Alternative Approach)
"""
Sometimes you need more control than generic views provide.
Function-based views give you complete control over the logic.
"""

@api_view(['POST', 'DELETE'])
@permission_classes([permissions.AllowAny])  # TODO: Change to IsAuthenticated
def post_like_toggle(request, post_id):
    """
    🎓 LEARNING: Function-Based API View
    
    Handles: POST /api/posts/1/like/ (like post)
             DELETE /api/posts/1/like/ (unlike post)
    Purpose: Toggle like status for Instagram-style heart button
    
    This is what your React PostCard heart button will call
    """
    
    # Get the post or return 404 if not found
    post = get_object_or_404(Post, id=post_id, is_active=True)
    
    # TODO: Use request.user when authentication is implemented
    from authentication.models import User
    user = User.objects.filter(username='athul_user').first()
    if not user:
        user = User.objects.first()
    
    if not user:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Check if user already liked this post
        like = PostLike.objects.get(user=user, post=post)
        
        if request.method == 'DELETE':
            # Unlike: Remove the like
            like.delete()
            is_liked = False
            message = "Post unliked successfully"
        else:
            # POST but already liked - return current status
            is_liked = True  
            message = "Post already liked"
            
    except PostLike.DoesNotExist:
        if request.method == 'POST':
            # Like: Create new like
            PostLike.objects.create(user=user, post=post)
            is_liked = True
            message = "Post liked successfully"
        else:
            # DELETE but not liked - return current status
            is_liked = False
            message = "Post not liked"
    
    # Return updated post data
    return Response({
        'success': True,
        'message': message,
        'is_liked': is_liked,
        'total_likes': post.total_likes,  # This updates automatically via signals!
        'post_id': post.id
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def post_stats(request, post_id):
    """
    🎓 LEARNING: Stats API Endpoint
    
    Handles: GET /api/posts/1/stats/
    Purpose: Get detailed statistics for a post
    Features: Like count, comment count, share count, recent likers
    
    Useful for showing "Liked by alex_photo and 42 others"
    """
    
    post = get_object_or_404(Post, id=post_id, is_active=True)
    
    # Get recent likers (for "Liked by X and Y" display)
    recent_likes = PostLike.objects.filter(post=post).select_related(
        'user'
    ).order_by('-created_at')[:3]
    
    recent_likers = [
        {
            'username': like.user.username,
            'full_name': like.user.full_name
        }
        for like in recent_likes
    ]
    
    # Check if current user liked this post (when auth is implemented)
    is_liked = False
    # TODO: Implement when authentication is added
    # if request.user.is_authenticated:
    #     is_liked = PostLike.objects.filter(
    #         user=request.user, 
    #         post=post
    #     ).exists()
    
    return Response({
        'post_id': post.id,
        'total_likes': post.total_likes,
        'total_comments': post.total_comments,
        'total_shares': post.total_shares,
        'is_liked': is_liked,
        'recent_likers': recent_likers,
        'created_at': post.created_at,
        'author': {
            'username': post.author.username,
            'full_name': post.author.full_name
        }
    })


class UserPostsAPIView(generics.ListAPIView):
    """
    🎓 LEARNING: User-Specific Posts
    
    Handles: GET /api/users/1/posts/
    Purpose: Get all posts by a specific user (for profile pages)
    Features: User profile post grid
    """
    
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Post.objects.filter(
            author_id=user_id, 
            is_active=True
        ).select_related(
            'author',
            'author__profile'
        ).order_by('-created_at')


# 🎓 LEARNING: Advanced API Features
"""
These views demonstrate several important concepts:

1. PERMISSIONS:
   - IsAuthenticated: Must be logged in
   - IsAuthenticatedOrReadOnly: Anyone can read, login required to write

2. QUERY OPTIMIZATION:
   - select_related(): Load related objects in same query (1-to-1, many-to-1)
   - prefetch_related(): Efficiently load many-to-many and reverse foreign keys

3. FILTERING & SEARCH:
   - Query parameters: ?author=1&search=sunset
   - Q objects: Complex OR/AND queries

4. ERROR HANDLING:
   - get_object_or_404(): Return 404 if object doesn't exist
   - Try/except: Handle edge cases gracefully

5. CUSTOM LOGIC:
   - perform_create(): Add behavior during object creation
   - get_queryset(): Customize which objects to return

These patterns work for any Django model, not just posts!
"""