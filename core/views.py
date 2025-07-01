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