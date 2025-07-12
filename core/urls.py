# UPDATED core/urls.py - ADD THESE NEW PATTERNS
# core/urls.py - CLEAN VERSION WITHOUT STORIES
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # 📊 POSTS ENDPOINTS
    
    # GET /api/posts/ - List posts for home feed
    path('posts/', views.PostListAPIView.as_view(), name='post-list'),
    
    # POST /api/posts/create/ - Create new post
    path('posts/create/', views.PostCreateAPIView.as_view(), name='post-create'),
    
    # GET /api/posts/1/ - Get single post with details
    path('posts/<int:pk>/', views.PostDetailAPIView.as_view(), name='post-detail'),
    
    # 🆕 NEW: POST EDIT/DELETE ENDPOINTS
    # PUT /api/posts/1/edit/ - Edit post (author only)
    path('posts/<int:pk>/edit/', views.PostUpdateAPIView.as_view(), name='post-edit'),
    
    # DELETE /api/posts/1/delete/ - Delete post (author only)  
    path('posts/<int:pk>/delete/', views.PostDeleteAPIView.as_view(), name='post-delete'),
    
    # ❤️ LIKE SYSTEM ENDPOINTS
    
    # POST /api/posts/1/like/ - Like a post
    # DELETE /api/posts/1/like/ - Unlike a post  
    path('posts/<int:post_id>/like/', views.post_like_toggle, name='post-like-toggle'),
    
    # GET /api/posts/1/stats/ - Get post statistics
    path('posts/<int:post_id>/stats/', views.post_stats, name='post-stats'),
    
    # 💬 COMMENT SYSTEM ENDPOINTS
    
    # GET /api/posts/1/comments/ - List comments for a post
    # POST /api/posts/1/comments/ - Add comment to a post
    path('posts/<int:post_id>/comments/', 
         views.PostCommentsListCreateAPIView.as_view(), 
         name='post-comments'),
    
    # GET /api/comments/1/ - Get specific comment
    # PUT /api/comments/1/ - Update comment (author only)
    # DELETE /api/comments/1/ - Delete comment (author only)
    path('comments/<int:pk>/', 
         views.CommentDetailAPIView.as_view(), 
         name='comment-detail'),
    
    # 👤 USER POSTS ENDPOINTS
    
    # GET /api/users/1/posts/ - Get all posts by specific user (for profile pages)
    path('users/<int:user_id>/posts/', views.UserPostsAPIView.as_view(), name='user-posts'),
]