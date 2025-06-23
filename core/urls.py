# core/urls.py
from django.urls import path
from . import views

# 🎓 LEARNING: API URL Patterns
"""
URL patterns map HTTP requests to view functions/classes
Format: path('endpoint/', ViewClass.as_view(), name='url_name')

RESTful API Conventions:
- GET /api/posts/ - List all posts
- POST /api/posts/ - Create new post  
- GET /api/posts/1/ - Get specific post
- PUT /api/posts/1/ - Update specific post
- DELETE /api/posts/1/ - Delete specific post

Custom actions:
- POST /api/posts/1/like/ - Like a post
- GET /api/posts/1/stats/ - Get post statistics
"""

app_name = 'core'  # Namespace for URL names

urlpatterns = [
    # 📊 POSTS ENDPOINTS
    
    # GET /api/posts/ - List posts for home feed
    # POST /api/posts/ - Create new post
    path('posts/', views.PostListAPIView.as_view(), name='post-list'),
    path('posts/create/', views.PostCreateAPIView.as_view(), name='post-create'),
    
    # GET /api/posts/1/ - Get single post with details
    path('posts/<int:pk>/', views.PostDetailAPIView.as_view(), name='post-detail'),
    
    # ❤️ LIKE SYSTEM ENDPOINTS
    
    # POST /api/posts/1/like/ - Like a post
    # DELETE /api/posts/1/like/ - Unlike a post  
    path('posts/<int:post_id>/like/', views.post_like_toggle, name='post-like-toggle'),
    
    # GET /api/posts/1/stats/ - Get post statistics
    path('posts/<int:post_id>/stats/', views.post_stats, name='post-stats'),
    
    # 👤 USER POSTS ENDPOINTS
    
    # GET /api/users/1/posts/ - Get all posts by specific user (for profile pages)
    path('users/<int:user_id>/posts/', views.UserPostsAPIView.as_view(), name='user-posts'),
]

# 🎓 LEARNING: URL Pattern Breakdown
"""
Let's understand each URL pattern:

1. path('posts/', views.PostListAPIView.as_view(), name='post-list')
   - 'posts/' = URL endpoint
   - views.PostListAPIView.as_view() = Class-based view converted to function
   - name='post-list' = Name for reverse URL lookup

2. path('posts/<int:pk>/', views.PostDetailAPIView.as_view(), name='post-detail')
   - <int:pk> = Captures integer from URL as 'pk' parameter
   - pk = primary key (standard Django convention)
   - URL: /api/posts/123/ captures pk=123

3. path('posts/<int:post_id>/like/', views.post_like_toggle, name='post-like-toggle')
   - <int:post_id> = Captures integer as 'post_id' parameter
   - Function-based view (no .as_view() needed)
   - URL: /api/posts/123/like/ captures post_id=123

URL Parameter Types:
- <int:id> = Integer (123)
- <str:username> = String (alex_photo)
- <slug:slug> = Slug (my-post-title)
- <uuid:id> = UUID (550e8400-e29b-41d4-a716-446655440000)
"""