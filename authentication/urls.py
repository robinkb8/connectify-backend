# authentication/urls.py - COMPLETE WITH ALL ENDPOINTS
from django.urls import path
from . import views

# URL patterns for authentication app
urlpatterns = [
    # ===== EXISTING ROUTES =====
    
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
    
    # ===== MISSING ROUTES - ADD THESE =====
    
    # Profile viewing (Change 1)
    path('users/<str:username>/', views.get_user_profile, name='get_user_profile'),
    
    # Follow/Unfollow system (Change 2)
    path('users/<int:user_id>/follow/', views.follow_user, name='follow_user'),
    path('users/<int:user_id>/unfollow/', views.unfollow_user, name='unfollow_user'),
    
    # Followers/Following lists (Change 4)
    path('users/<int:user_id>/followers/', views.get_user_followers, name='get_user_followers'),
    path('users/<int:user_id>/following/', views.get_user_following, name='get_user_following'),
]