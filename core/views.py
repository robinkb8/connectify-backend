# core/views.py
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

from .models import Post, PostLike
from .serializers import (
    PostSerializer, 
    PostCreateSerializer, 
    PostDetailSerializer
)

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
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def perform_create(self, serializer):
        """Set author automatically"""
        from authentication.models import User
        
        # Use existing user
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


# 🎓 LEARNING: Function-Based API Views (Alternative Approach)
"""
Sometimes you need more control than generic views provide.
Function-based views give you complete control over the logic.
"""

@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
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
    user = request.user
    
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
    
    # Check if current user liked this post
    is_liked = False
    if request.user.is_authenticated:
        is_liked = PostLike.objects.filter(
            user=request.user, 
            post=post
        ).exists()
    
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