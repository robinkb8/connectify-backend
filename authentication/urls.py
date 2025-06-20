from django.urls import path
from . import views

# URL patterns for authentication app
urlpatterns = [
    # User Registration Endpoint
    path('register/', views.register_user, name='register_user'),
    
    # User Login Endpoint  
    path('login/', views.login_user, name='login_user'),
    
    # Username Availability Check
    path('check-username/', views.check_username_availability, name='check_username'),
    
    # Email Availability Check
    path('check-email/', views.check_email_availability, name='check_email'),

      # ✅ ADD THESE NEW OTP ENDPOINTS:
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
]