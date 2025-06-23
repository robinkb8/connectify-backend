# core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    UserProfile, Post, PostLike, Comment, 
    Story, StoryView, Follow, PostShare
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User Profile management in admin"""
    list_display = [
        'user_link',
        'followers_count',
        'following_count', 
        'posts_count',
        'is_private',
        'created_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'user__full_name',
        'location'
    ]
    
    list_filter = [
        'is_private',
        'created_at',
        'location'
    ]
    
    readonly_fields = [
        'followers_count', 
        'following_count', 
        'posts_count',
        'created_at',
        'updated_at',
        'avatar_preview'
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'bio', 'location', 'website')
        }),
        ('Avatar', {
            'fields': ('avatar', 'avatar_preview')
        }),
        ('Privacy Settings', {
            'fields': ('is_private',)
        }),
        ('Statistics', {
            'fields': ('followers_count', 'following_count', 'posts_count'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        """Clickable link to user"""
        url = reverse('admin:authentication_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Username'
    user_link.admin_order_field = 'user__username'
    
    def avatar_preview(self, obj):
        """Show avatar preview"""
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return "No avatar"
    avatar_preview.short_description = 'Avatar Preview'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Post management in admin"""
    list_display = [
        'id',
        'author_link',
        'content_preview',
        'total_likes',
        'total_comments',
        'is_active',
        'created_at'
    ]
    
    search_fields = [
        'content',
        'author__username',
        'author__full_name'
    ]
    
    list_filter = [
        'is_active',
        'is_featured',
        'created_at',
        'author'
    ]
    
    readonly_fields = [
        'total_likes',
        'total_comments', 
        'total_shares',
        'created_at',
        'updated_at',
        'image_preview'
    ]
    
    fieldsets = (
        ('Post Content', {
            'fields': ('author', 'content', 'image', 'image_preview')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Statistics', {
            'fields': ('total_likes', 'total_comments', 'total_shares'),
            'classes': ('collapse',)
        }),
    )
    
    def author_link(self, obj):
        """Link to author"""
        url = reverse('admin:authentication_user_change', args=[obj.author.id])
        return format_html('<a href="{}">{}</a>', url, obj.author.username)
    author_link.short_description = 'Author'
    author_link.admin_order_field = 'author__username'
    
    def content_preview(self, obj):
        """Show first 50 characters"""
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def image_preview(self, obj):
        """Show image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 60px; object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Image Preview'


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    """Post Like management (Instagram-style hearts)"""
    list_display = [
        'user_link',
        'post_link', 
        'created_at'
    ]
    
    search_fields = [
        'user__username',
        'post__content'
    ]
    
    list_filter = [
        'created_at',
        'post__author'
    ]
    
    readonly_fields = ['created_at']
    
    def user_link(self, obj):
        """Link to user who liked"""
        url = reverse('admin:authentication_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def post_link(self, obj):
        """Link to liked post"""
        url = reverse('admin:core_post_change', args=[obj.post.id])
        content_preview = obj.post.content[:30] + "..." if len(obj.post.content) > 30 else obj.post.content
        return format_html('<a href="{}">Post: {}</a>', url, content_preview)
    post_link.short_description = 'Post'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Comment management"""
    list_display = [
        'author_link',
        'post_link',
        'content_preview',
        'parent_comment',
        'created_at'
    ]
    
    search_fields = [
        'content',
        'author__username',
        'post__content'
    ]
    
    list_filter = [
        'created_at',
        'post__author'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    def author_link(self, obj):
        url = reverse('admin:authentication_user_change', args=[obj.author.id])
        return format_html('<a href="{}">{}</a>', url, obj.author.username)
    author_link.short_description = 'Author'
    
    def post_link(self, obj):
        url = reverse('admin:core_post_change', args=[obj.post.id])
        return format_html('<a href="{}">Post #{}</a>', url, obj.post.id)
    post_link.short_description = 'Post'
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Comment'


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    """Story management (24-hour expiring content)"""
    list_display = [
        'author_link',
        'caption_preview',
        'total_views',
        'is_expired_status',
        'created_at',
        'expires_at'
    ]
    
    search_fields = [
        'caption',
        'author__username'
    ]
    
    list_filter = [
        'created_at',
        'expires_at'
    ]
    
    readonly_fields = [
        'total_views',
        'created_at',
        'image_preview',
        'is_expired_status'
    ]
    
    def author_link(self, obj):
        url = reverse('admin:authentication_user_change', args=[obj.author.id])
        return format_html('<a href="{}">{}</a>', url, obj.author.username)
    author_link.short_description = 'Author'
    
    def caption_preview(self, obj):
        return obj.caption[:30] + "..." if len(obj.caption) > 30 else obj.caption or "No caption"
    caption_preview.short_description = 'Caption'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px; object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Story Image'
    
    def is_expired_status(self, obj):
        """Show if story is expired"""
        expired = obj.is_expired()
        color = 'red' if expired else 'green'
        text = 'Expired' if expired else 'Active'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, text
        )
    is_expired_status.short_description = 'Status'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Following relationships management"""
    list_display = [
        'follower_link',
        'following_link',
        'created_at'
    ]
    
    search_fields = [
        'follower__username',
        'following__username'
    ]
    
    list_filter = ['created_at']
    
    readonly_fields = ['created_at']
    
    def follower_link(self, obj):
        url = reverse('admin:authentication_user_change', args=[obj.follower.id])
        return format_html('<a href="{}">{}</a>', url, obj.follower.username)
    follower_link.short_description = 'Follower'
    
    def following_link(self, obj):
        url = reverse('admin:authentication_user_change', args=[obj.following.id])
        return format_html('<a href="{}">{}</a>', url, obj.following.username)
    following_link.short_description = 'Following'


@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    """Story views tracking"""
    list_display = [
        'viewer_link',
        'story_link',
        'viewed_at'
    ]
    
    search_fields = [
        'viewer__username',
        'story__author__username'
    ]
    
    list_filter = ['viewed_at']
    
    readonly_fields = ['viewed_at']
    
    def viewer_link(self, obj):
        url = reverse('admin:authentication_user_change', args=[obj.viewer.id])
        return format_html('<a href="{}">{}</a>', url, obj.viewer.username)
    viewer_link.short_description = 'Viewer'
    
    def story_link(self, obj):
        url = reverse('admin:core_story_change', args=[obj.story.id])
        return format_html('<a href="{}">Story by {}</a>', url, obj.story.author.username)
    story_link.short_description = 'Story'


@admin.register(PostShare)
class PostShareAdmin(admin.ModelAdmin):
    """Post shares tracking"""
    list_display = [
        'user_link',
        'post_link',
        'shared_at'
    ]
    
    search_fields = [
        'user__username',
        'post__content'
    ]
    
    list_filter = ['shared_at']
    
    readonly_fields = ['shared_at']
    
    def user_link(self, obj):
        url = reverse('admin:authentication_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def post_link(self, obj):
        url = reverse('admin:core_post_change', args=[obj.post.id])
        content_preview = obj.post.content[:30] + "..." if len(obj.post.content) > 30 else obj.post.content
        return format_html('<a href="{}">Post: {}</a>', url, content_preview)
    post_link.short_description = 'Post'


# Customize admin site headers
admin.site.site_header = "Connectify Admin Dashboard"
admin.site.site_title = "Connectify Admin"
admin.site.index_title = "Welcome to Connectify Social Media Administration"