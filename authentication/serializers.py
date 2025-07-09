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

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user data with pro status information
    """
    pro_status_display = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'full_name', 'phone', 
            'is_active', 'date_joined', 'is_pro', 'pro_upgraded_at', 
            'pro_status_display'
        )
        read_only_fields = ('id', 'date_joined', 'is_pro', 'pro_upgraded_at', 'pro_status_display')