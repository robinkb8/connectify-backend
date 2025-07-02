# authentication/urls.py - CHANGE 1B: Add Profile URL Route
# ALL EXISTING ROUTES PRESERVED - ONLY ADDING ONE NEW ROUTE

from django.urls import path
from . import views

# URL patterns for authentication app
urlpatterns = [
    # ===== ALL EXISTING ROUTES PRESERVED =====
    
    # User Registration Endpoint
    path('register/', views.register_user, name='register_user'),
    
    # User Login Endpoint  
    path('login/', views.login_user, name='login_user'),
    
    # Username Availability Check
    path('check-username/', views.check_username_availability, name='check_username'),
    
    # Email Availability Check
    path('check-email/', views.check_email_availability, name='check_email'),

    # OTP Endpoints
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    # Email exists check (for Google Sign-In)
    path('api/auth/check-email/', views.check_email_exists),
    
    # Current user profile
    path('me/', views.current_user, name='current_user'),
    
    # Profile management
    path('profile/update/', views.update_user_profile, name='update_user_profile'),
    path('profile/avatar/', views.upload_avatar, name='upload_avatar'),
    
    # ===== NEW ROUTE - CHANGE 1B =====
    
    # Get any user's profile by username
    path('users/<str:username>/', views.get_user_profile, name='get_user_profile'),
]