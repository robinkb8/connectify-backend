from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone

from .serializers import UserRegistrationSerializer
from .models import User, EmailOTP
from .email_service import generate_otp, send_otp_email


@api_view(['POST'])
@permission_classes([])
def check_email_exists(request):
    """Check if user with this email exists (used for Google Sign-In)"""
    email = request.data.get('email', '').strip().lower()

    if not email:
        return Response({
            'available': False,
            'exists': False,
            'message': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    user_exists = User.objects.filter(email=email).exists()

    return Response({
        'available': not user_exists,
        'exists': user_exists,
        'message': 'User found' if user_exists else 'User not found'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([])
def register_user(request):
    """Handle user registration with JWT token generation"""
    data = request.data
    serializer = UserRegistrationSerializer(data=data)
    
    if serializer.is_valid():
        try:
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            return Response({
                'success': True,
                'message': 'Account created successfully!',
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh),
                },
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'full_name': user.full_name
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to create account: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    else:
        return Response({
            'success': False,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([])
def login_user(request):
    """Handle user login with JWT token generation"""
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')
    
    if not email or not password:
        return Response({
            'success': False,
            'message': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        if user.check_password(password):
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            return Response({
                'success': True,
                'message': 'Login successful!',
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh),
                },
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'full_name': user.full_name
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Invalid email or password'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Login failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Get current authenticated user info"""
    user = request.user
    return Response({
        'success': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'full_name': user.full_name
        }
    })


@api_view(['POST'])
@permission_classes([])
def check_username_availability(request):
    """Check if username is available"""
    username = request.data.get('username', '').strip().lower()
    
    if not username:
        return Response({
            'available': False,
            'message': 'Username is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({
            'available': False,
            'message': 'Username is already taken'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'available': True,
        'message': 'Username is available!'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([])
def check_email_availability(request):
    """Check if email is available"""
    email = request.data.get('email', '').strip().lower()
    
    if not email:
        return Response({
            'available': False,
            'message': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=email).exists():
        return Response({
            'available': False,
            'message': 'Email is already registered'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'available': True,
        'message': 'Email is available!'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([])
def send_otp(request):
    """Send OTP email using AWS SES"""
    email = request.data.get('email', '').strip().lower()
    
    if not email:
        return Response({
            'success': False,
            'message': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        otp_code = generate_otp()
        
        EmailOTP.objects.create(
            email=email,
            otp_code=otp_code
        )
        
        email_sent = send_otp_email(email, otp_code)
        
        if email_sent:
            return Response({
                'success': True,
                'message': f'OTP sent to {email}'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Failed to send email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error sending OTP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])
def verify_otp(request):
    """Verify OTP code from database"""
    email = request.data.get('email', '').strip().lower()
    otp_code = request.data.get('otp_code', '').strip()
    
    if not email or not otp_code:
        return Response({
            'success': False,
            'message': 'Email and OTP code are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        otp_record = EmailOTP.objects.filter(
            email=email,
            otp_code=otp_code,
            is_used=False
        ).first()
        
        if not otp_record:
            return Response({
                'success': False,
                'message': 'Invalid OTP code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if otp_record.is_expired():
            return Response({
                'success': False,
                'message': 'OTP has expired. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        otp_record.is_used = True
        otp_record.save()
        
        return Response({
            'success': True,
            'message': 'OTP verified successfully!'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error verifying OTP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)