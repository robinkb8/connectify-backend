# core/admin.py - CLEAN VERSION WITHOUT STORIES
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Post, PostLike, Comment, UserProfile, Follow, PostShare

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Post management in admin"""
    list_display = [
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
        'created_at',
        'author'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'total_likes', 'total_comments']
    
    def author_link(self, obj):
        url = reverse('admin:authentication_user_change', args=[obj.author.id])
        return format_html('<a href="{}">{}</a>', url, obj.author.username)
    author_link.short_description = 'Author'
    author_link.admin_order_field = 'author__username'
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    """Like management"""
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
        url = reverse('admin:authentication_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def post_link(self, obj):
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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User profile management"""
    list_display = [
        'user_link',
        'followers_count',
        'following_count',
        'posts_count',
        'is_private'
    ]
    
    def user_link(self, obj):
        url = reverse('admin:authentication_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'


admin.site.site_header = "Connectify Admin"
admin.site.site_title = "Connectify"
admin.site.index_title = "Welcome to Connectify Administration"