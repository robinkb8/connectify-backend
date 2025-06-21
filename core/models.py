# core/models.py
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
        null=True
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


class Story(models.Model):
    """Instagram-style stories that expire after 24 hours"""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stories'
    )
    image = models.ImageField(upload_to='stories/images/%Y/%m/%d/')
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    total_views = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'stories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['expires_at']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Set expiration to 24 hours if not provided
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Story by {self.author.username} - {self.created_at}"


class StoryView(models.Model):
    """Track who viewed which stories"""
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name='views'
    )
    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'story_views'
        unique_together = ['story', 'viewer']
        indexes = [
            models.Index(fields=['story', 'viewed_at']),
        ]
    
    def __str__(self):
        return f"{self.viewer.username} viewed story {self.story.id}"


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
@receiver(post_delete, sender=PostLike)
def update_post_like_count(sender, instance, **kwargs):
    """Update post like count when likes change"""
    post = instance.post
    post.total_likes = post.likes.count()
    post.save(update_fields=['total_likes'])

@receiver(post_save, sender=Comment)
@receiver(post_delete, sender=Comment)
def update_post_comment_count(sender, instance, **kwargs):
    """Update post comment count when comments change"""
    post = instance.post
    post.total_comments = post.comments.count()
    post.save(update_fields=['total_comments'])

@receiver(post_save, sender=PostShare)
@receiver(post_delete, sender=PostShare)
def update_post_share_count(sender, instance, **kwargs):
    """Update post share count when shares change"""
    post = instance.post
    post.total_shares = post.shares.count()
    post.save(update_fields=['total_shares'])

@receiver(post_save, sender=Follow)
@receiver(post_delete, sender=Follow)
def update_follow_counts(sender, instance, **kwargs):
    """Update follower/following counts when follows change"""
    # Update follower's following count
    follower_profile, _ = UserProfile.objects.get_or_create(user=instance.follower)
    follower_profile.following_count = instance.follower.following.count()
    follower_profile.save(update_fields=['following_count'])
    
    # Update following's follower count
    following_profile, _ = UserProfile.objects.get_or_create(user=instance.following)
    following_profile.followers_count = instance.following.followers.count()
    following_profile.save(update_fields=['followers_count'])

@receiver(post_save, sender=Post)
@receiver(post_delete, sender=Post)
def update_user_posts_count(sender, instance, **kwargs):
    """Update user's posts count when posts change"""
    profile, _ = UserProfile.objects.get_or_create(user=instance.author)
    profile.posts_count = instance.author.posts.filter(is_active=True).count()
    profile.save(update_fields=['posts_count'])