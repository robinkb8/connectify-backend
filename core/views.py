from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import Post, PostLike, Comment
from .serializers import (
    PostSerializer, 
    PostCreateSerializer, 
    PostDetailSerializer,
    PostUpdateSerializer,
    CommentSerializer,
    CommentCreateSerializer
)


class PostListAPIView(generics.ListAPIView):
    """GET /api/posts/ - Return posts for the home feed"""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Get active posts with optimized queries"""
        queryset = Post.objects.filter(
            is_active=True
        ).select_related(
            'author',
            'author__profile'
        ).prefetch_related(
            'likes',
            'comments'
        ).order_by('-created_at')
        
        return queryset


class PostCreateAPIView(generics.CreateAPIView):
    """POST /api/posts/create/ - Create new post with optional image upload"""
    serializer_class = PostCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def perform_create(self, serializer):
        """Set author when creating post"""
        post = serializer.save(author=self.request.user)


class PostDetailAPIView(generics.RetrieveAPIView):
    """GET /api/posts/1/ - Get single post with comments and details"""
    serializer_class = PostDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Get post with optimized queries"""
        return Post.objects.select_related(
            'author',
            'author__profile'
        ).prefetch_related(
            'comments__author',
            'comments__author__profile',
            'likes__user'
        )


class UserPostsAPIView(generics.ListAPIView):
    """GET /api/users/1/posts/ - Get all posts by a specific user"""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Get user's posts"""
        user_id = self.kwargs['user_id']
        return Post.objects.filter(
            author_id=user_id,
            is_active=True
        ).select_related(
            'author',
            'author__profile'
        ).order_by('-created_at')


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def post_like_toggle(request, post_id):
    """POST/DELETE /api/posts/1/like/ - Like or unlike a post"""
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    
    if request.method == 'POST':
        like, created = PostLike.objects.get_or_create(
            user=user,
            post=post
        )
        
        if created:
            return Response({
                'success': True,
                'message': 'Post liked',
                'is_liked': True,
                'total_likes': post.total_likes
            })
        else:
            return Response({
                'success': False,
                'message': 'Already liked'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        try:
            like = PostLike.objects.get(user=user, post=post)
            like.delete()
            
            return Response({
                'success': True,
                'message': 'Post unliked',
                'is_liked': False,
                'total_likes': post.total_likes
            })
        except PostLike.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Not liked yet'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def post_stats(request, post_id):
    """GET /api/posts/1/stats/ - Get detailed post statistics"""
    post = get_object_or_404(Post, id=post_id)
    
    return Response({
        'post_id': post.id,
        'total_likes': post.total_likes,
        'total_comments': post.total_comments,
        'total_shares': post.total_shares,
        'created_at': post.created_at,
        'is_active': post.is_active
    })

class PostUpdateAPIView(generics.RetrieveUpdateAPIView):
    """PUT /api/posts/1/edit/ - Update post (author only)"""
    serializer_class = PostUpdateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        """Get post with optimized queries"""
        return Post.objects.select_related(
            'author',
            'author__profile'
        )
    
    def perform_update(self, serializer):
        """Update post (only by author)"""
        post = self.get_object()
        if post.author != self.request.user:
            return Response({
                'success': False,
                'message': 'You can only edit your own posts'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Save the updated post
        updated_post = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Post updated successfully',
            'post': PostSerializer(updated_post, context={'request': self.request}).data
        })


class PostDeleteAPIView(generics.DestroyAPIView):
    """DELETE /api/posts/1/delete/ - Delete post (author only)"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get post with optimized queries"""
        return Post.objects.select_related('author')
    
    def perform_destroy(self, instance):
        """Delete post (only by author)"""
        if instance.author != self.request.user:
            return Response({
                'success': False,
                'message': 'You can only delete your own posts'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Soft delete - mark as inactive instead of hard delete
        instance.is_active = False
        instance.save(update_fields=['is_active'])
    
    def destroy(self, request, *args, **kwargs):
        """Custom destroy method with proper response"""
        instance = self.get_object()
        
        # Check ownership
        if instance.author != request.user:
            return Response({
                'success': False,
                'message': 'You can only delete your own posts'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Perform soft delete
        self.perform_destroy(instance)
        
        return Response({
            'success': True,
            'message': 'Post deleted successfully'
        }, status=status.HTTP_200_OK)


class PostCommentsListCreateAPIView(generics.ListCreateAPIView):
    """GET/POST /api/posts/1/comments/ - List comments for a post or add new comment"""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Get comments for specific post"""
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(
            post_id=post_id
        ).select_related(
            'author',
            'author__profile'
        ).order_by('created_at')
    
    def get_serializer_class(self):
        """Use different serializer for creation"""
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer
    
    def perform_create(self, serializer):
        """Set author and post when creating comment"""
        post_id = self.kwargs['post_id']
        post = get_object_or_404(Post, id=post_id)
        comment = serializer.save(author=self.request.user, post=post)


class CommentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/comments/1/ - Get, update, or delete specific comment"""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get comment with optimized queries"""
        return Comment.objects.select_related(
            'author',
            'author__profile',
            'post'
        )
    
    def get_serializer_class(self):
        """Use different serializer for updates"""
        if self.request.method in ['PUT', 'PATCH']:
            return CommentCreateSerializer
        return CommentSerializer
    
    def perform_update(self, serializer):
        """Update comment (only by author)"""
        comment = self.get_object()
        if comment.author != self.request.user:
            return Response({
                'success': False,
                'message': 'You can only edit your own comments'
            }, status=status.HTTP_403_FORBIDDEN)
        serializer.save()
    
    def perform_destroy(self, instance):
        """Delete comment (only by author)"""
        if instance.author != self.request.user:
            return Response({
                'success': False,
                'message': 'You can only delete your own comments'
            }, status=status.HTTP_403_FORBIDDEN)
        instance.delete()