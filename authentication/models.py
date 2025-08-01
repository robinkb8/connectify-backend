from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta

class UserManager(BaseUserManager):
    """
    Custom manager for our User model
    This tells Django HOW to create users
    """
    
    def create_user(self, email, username, full_name, phone, password=None, **extra_fields):
        """
        Create and return a regular user
        """
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')
        if not full_name:
            raise ValueError('Users must have a full name')
        if not phone:
            raise ValueError('Users must have a phone number')
        
        # Normalize email (make it lowercase)
        email = self.normalize_email(email)
        
        # Create user instance
        user = self.model(
            email=email,
            username=username,
            full_name=full_name,
            phone=phone,
            **extra_fields
        )
        
        # Set password (this encrypts it)
        user.set_password(password)
        
        # Save to database
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, full_name, phone, password=None, **extra_fields):
        """
        Create and return a superuser (admin)
        """
        # Set superuser permissions
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, username, full_name, phone, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model that matches our React frontend form
    """
    
    email = models.EmailField(
        unique=True,
        max_length=254,
        help_text="User's email address - used for login"
    )
    
    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9._]*$',
                message='Username can only contain letters, numbers, dots, and underscores'
            )
        ],
        help_text="Unique username for the user"
    )
    
    full_name = models.CharField(
        max_length=50,
        help_text="User's full name"
    )
    
    phone_validator = RegexValidator(
        regex=r'^[6-9]\d{9}$',
        message="Phone number must be 10 digits starting with 6, 7, 8, or 9"
    )
    phone = models.CharField(
        max_length=10,
        validators=[phone_validator],
        unique=True,
        help_text="10-digit Indian mobile number"
    )
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # Pro subscription fields
    is_pro = models.BooleanField(default=False)
    pro_upgraded_at = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name', 'phone']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    def upgrade_to_pro(self):
        """Upgrade user to pro status"""
        self.is_pro = True
        self.pro_upgraded_at = timezone.now()
        self.save(update_fields=['is_pro', 'pro_upgraded_at'])
    
    def downgrade_from_pro(self):
        """Downgrade user from pro status"""
        self.is_pro = False
        self.save(update_fields=['is_pro'])
    
    @property
    def pro_status_display(self):
        """Human readable pro status"""
        return "Pro User" if self.is_pro else "Free User"

class EmailOTP(models.Model):
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'email_otps'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"OTP for {self.email} - {self.otp_code}"