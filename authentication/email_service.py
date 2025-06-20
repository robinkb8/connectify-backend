import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP email using AWS SES"""
    subject = 'Verify your Connectify account'
    message = f'''
    Hi there!
    
    Welcome to Connectify! Your verification code is:
    
    {otp}
    
    This code will expire in 10 minutes.
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    The Connectify Team
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False