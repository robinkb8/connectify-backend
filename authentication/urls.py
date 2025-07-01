from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # User Registration & Login
    path('register/', views.register_user, name='register_user'),
    path('login/', views.login_user, name='login_user'),
    
    # JWT Token Management
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Current User Info
    path('me/', views.current_user, name='current_user'),
    
    # Profile Management
    path('profile/update/', views.update_user_profile, name='update_profile'),
    path('profile/avatar/', views.upload_avatar, name='upload_avatar'),
    
    # Validation Endpoints
    path('check-username/', views.check_username_availability, name='check_username'),
    path('check-email/', views.check_email_availability, name='check_email'),
    
    # OTP Endpoints
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    
    # Google Sign-In Support
    path('api/auth/check-email/', views.check_email_exists),
]