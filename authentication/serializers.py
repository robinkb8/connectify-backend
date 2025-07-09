from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    Converts JSON data from React frontend to Django User model
    """
    
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ('email', 'username', 'full_name', 'phone', 'password', 'confirm_password')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'full_name': {'required': True},
            'phone': {'required': True},
        }
    
    def validate(self, attrs):
        """
        Custom validation for the entire serializer
        """
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        
        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")
        
        validate_password(password)
        
        attrs.pop('confirm_password', None)
        return attrs
    
    def create(self, validated_data):
        """
        Create and return a new user instance
        """
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.Serializer):
    """
    Serializer for UserProfile data
    """
    bio = serializers.CharField(allow_blank=True)
    avatar = serializers.SerializerMethodField()
    website = serializers.URLField(allow_blank=True)
    location = serializers.CharField(allow_blank=True)
    is_private = serializers.BooleanField()
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()
    posts_count = serializers.IntegerField()
    
    def get_avatar(self, profile):
        """Get avatar URL or None"""
        if profile.avatar:
            return profile.avatar.url
        return None


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user data with pro status and complete profile information
    """
    pro_status_display = serializers.ReadOnlyField()
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'full_name', 'phone', 
            'is_active', 'date_joined', 'is_pro', 'pro_upgraded_at', 
            'pro_status_display', 'profile'
        )
        read_only_fields = ('id', 'date_joined', 'is_pro', 'pro_upgraded_at', 'pro_status_display')
    
    def get_profile(self, user):
        """Get complete profile data"""
        try:
            if hasattr(user, 'profile'):
                profile_serializer = UserProfileSerializer(user.profile)
                return profile_serializer.data
            else:
                # Create profile if it doesn't exist
                from core.models import UserProfile
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile_serializer = UserProfileSerializer(profile)
                return profile_serializer.data
        except Exception as e:
            # Fallback profile data structure
            return {
                'bio': '',
                'avatar': None,
                'website': '',
                'location': '',
                'is_private': False,
                'followers_count': 0,
                'following_count': 0,
                'posts_count': 0,
            }