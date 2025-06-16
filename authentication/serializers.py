from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    Converts JSON data from React frontend to Django User model
    """
    
    # Password fields (write-only for security)
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
        
        # Check if passwords match
        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Use Django's built-in password validation
        validate_password(password)
        
        # Remove confirm_password as it's not needed for user creation
        attrs.pop('confirm_password', None)
        return attrs
    
    def create(self, validated_data):
        """
        Create and return a new user instance
        """
        # Use our custom UserManager to create user
        user = User.objects.create_user(**validated_data)
        return user