# core/models.py - CLEAN VERSION WITHOUT STORIES
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinLengthValidator
from PIL import Image
from datetime import timedelta

class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=50, blank=True)
    is_private = models.BooleanField(default=False)
    
    # Auto-calculated metrics
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    posts_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"Profile of {self.user.username}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Resize avatar if too large
        if self.avatar:
            img = Image.open(self.avatar.path)
            if img.height > 300 or img.width > 300:
                img.thumbnail((300, 300))
                img.save(self.avatar.path)


class Post(models.Model):
    """User posts in the feed"""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    content = models.TextField(
        max_length=2200,
        validators=[MinLengthValidator(1)]
    )
     
    image = models.ImageField(
        upload_to='posts/images/%Y/%m/%d/',
        blank=True,
        null=True,
        max_length=500
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Auto-calculated engagement metrics
    total_likes = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)
    total_shares = models.IntegerField(default=0)
    
    # Post status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'posts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"Post by {self.author.username} - {self.content[:50]}..."
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Resize post image if too large
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 800 or img.width > 800:
                img.thumbnail((800, 800))
                img.save(self.image.path)


class PostLike(models.Model):
    """Instagram-style like system for posts"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'post_likes'
        unique_together = ['user', 'post']  # One like per user per post
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} liked post {self.post.id}"


class Comment(models.Model):
    """Comments on posts with support for replies"""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField(
        max_length=500,
        validators=[MinLengthValidator(1)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For nested comments (replies)
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='replies'
    )
    
    class Meta:
        db_table = 'comments'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['parent_comment']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.username} on post {self.post.id}"


class Follow(models.Model):
    """User following relationships"""
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following'
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'follows'
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower']),
            models.Index(fields=['following']),
        ]
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class PostShare(models.Model):
    """Track post shares"""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    shared_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'post_shares'
        unique_together = ['post', 'user']
    
    def __str__(self):
        return f"{self.user.username} shared post {self.post.id}"


# Django Signals - Auto-update counts when data changes
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=PostLike)
def update_post_likes_on_like(sender, instance, created, **kwargs):
    """Update post likes count when a like is added"""
    if created:
        instance.post.total_likes = instance.post.likes.count()
        instance.post.save(update_fields=['total_likes'])
        
        # Create notification for post author
        from notifications.utils import create_like_notification
        create_like_notification(instance)

@receiver(post_delete, sender=PostLike)
def update_post_likes_on_unlike(sender, instance, **kwargs):
    """Update post likes count when a like is removed"""
    instance.post.total_likes = instance.post.likes.count()
    instance.post.save(update_fields=['total_likes'])

@receiver(post_save, sender=Comment)
def update_post_comments_on_add(sender, instance, created, **kwargs):
    """Update post comments count when a comment is added"""
    if created:
        instance.post.total_comments = instance.post.comments.count()
        instance.post.save(update_fields=['total_comments'])
        
        # Create notification for post author and mentioned users
        from notifications.utils import create_comment_notification
        create_comment_notification(instance)

@receiver(post_delete, sender=Comment)
def update_post_comments_on_delete(sender, instance, **kwargs):
    """Update post comments count when a comment is deleted"""
    instance.post.total_comments = instance.post.comments.count()
    instance.post.save(update_fields=['total_comments'])

@receiver(post_save, sender=Post)
def update_user_posts_count_on_create(sender, instance, created, **kwargs):
    """Update user's posts count when a post is created"""
    if created:
        # Ensure profile exists
        if hasattr(instance.author, 'profile'):
            # Recalculate posts count for the author
            posts_count = Post.objects.filter(author=instance.author).count()
            instance.author.profile.posts_count = posts_count
            instance.author.profile.save(update_fields=['posts_count'])

@receiver(post_delete, sender=Post)
def update_user_posts_count_on_delete(sender, instance, **kwargs):
    """Update user's posts count when a post is deleted"""
    # Ensure profile exists
    if hasattr(instance.author, 'profile'):
        # Recalculate posts count for the author
        posts_count = Post.objects.filter(author=instance.author).count()
        instance.author.profile.posts_count = posts_count
        instance.author.profile.save(update_fields=['posts_count'])

@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    """Create notification when user follows another user"""
    if created:
        from notifications.utils import create_follow_notification
        create_follow_notification(instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create UserProfile when new user is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Save profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # Create profile if it doesn't exist (for existing users)
        UserProfile.objects.get_or_create(user=instance)