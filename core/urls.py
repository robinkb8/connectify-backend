# core/urls.py - UPDATED WITH STORIES ENDPOINTS
from django.urls import path
from . import views

# 🎓 LEARNING: Complete Social Media API URL Patterns
"""
URL patterns map HTTP requests to view functions/classes
Format: path('endpoint/', ViewClass.as_view(), name='url_name')

Complete Social Media API:
- Posts (create, list, like, comment)
- Stories (create, list, view, track)
- Comments (create, list, update, delete)
- User interactions (likes, follows, shares)
"""

app_name = 'core'  # Namespace for URL names

urlpatterns = [
    # 📊 POSTS ENDPOINTS
    
    # GET /api/posts/ - List posts for home feed
    path('posts/', views.PostListAPIView.as_view(), name='post-list'),
    
    # POST /api/posts/create/ - Create new post
    path('posts/create/', views.PostCreateAPIView.as_view(), name='post-create'),
    
    # GET /api/posts/1/ - Get single post with details
    path('posts/<int:pk>/', views.PostDetailAPIView.as_view(), name='post-detail'),
    
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
    
    # 📸 STORIES SYSTEM ENDPOINTS
    
    # GET /api/stories/ - List active stories for stories section
    path('stories/', views.StoriesListAPIView.as_view(), name='stories-list'),
    
    # POST /api/stories/create/ - Create new story with image
    path('stories/create/', views.StoryCreateAPIView.as_view(), name='story-create'),
    
    # GET /api/stories/1/ - Get single story with details and viewers
    path('stories/<int:pk>/', views.StoryDetailAPIView.as_view(), name='story-detail'),
    
    # POST /api/stories/1/view/ - Mark story as viewed by current user
    path('stories/<int:story_id>/view/', views.mark_story_viewed, name='story-view'),
    
    # GET /api/stories/1/stats/ - Get story statistics and viewers
    path('stories/<int:story_id>/stats/', views.stories_stats, name='story-stats'),
    
    # GET /api/users/1/stories/ - Get all stories by specific user
    path('users/<int:user_id>/stories/', views.user_stories, name='user-stories'),
    
    # 👤 USER POSTS ENDPOINTS
    
    # GET /api/users/1/posts/ - Get all posts by specific user (for profile pages)
    path('users/<int:user_id>/posts/', views.UserPostsAPIView.as_view(), name='user-posts'),
]

# 🎓 LEARNING: Complete API Reference
"""
POSTS API:
✅ GET    /api/posts/                 - List posts (feed)
✅ POST   /api/posts/create/          - Create post
✅ GET    /api/posts/1/               - Get post details
✅ GET    /api/users/1/posts/         - Get user's posts

LIKES API:
✅ POST   /api/posts/1/like/          - Like a post
✅ DELETE /api/posts/1/like/          - Unlike a post
✅ GET    /api/posts/1/stats/         - Get post stats

COMMENTS API:
✅ GET    /api/posts/1/comments/      - List post comments
✅ POST   /api/posts/1/comments/      - Add comment
✅ GET    /api/comments/1/            - Get comment
✅ PUT    /api/comments/1/            - Update comment
✅ DELETE /api/comments/1/            - Delete comment

STORIES API:
✅ GET    /api/stories/               - List active stories
✅ POST   /api/stories/create/        - Create new story
✅ GET    /api/stories/1/             - Get story details
✅ POST   /api/stories/1/view/        - Mark story as viewed
✅ GET    /api/stories/1/stats/       - Get story statistics
✅ GET    /api/users/1/stories/       - Get user's stories

URL Parameter Examples:
- /api/posts/123/like/              → post_id = 123
- /api/stories/456/view/            → story_id = 456
- /api/users/789/stories/           → user_id = 789
- /api/comments/101/                → pk = 101 (comment id)

HTTP Methods:
- GET: Retrieve data (read-only)
- POST: Create new data or trigger actions
- PUT: Update existing data (full update)
- PATCH: Partial update
- DELETE: Remove data

Response Format (JSON):
{
  "success": true,
  "message": "Operation successful",
  "data": { ... },
  "errors": null
}

Instagram-Like Features:
🎯 24-hour story expiration
🎯 Story view tracking
🎯 Real-time engagement counts
🎯 Image upload with validation
🎯 User activity feeds
🎯 Social interactions (likes, comments, follows)
"""