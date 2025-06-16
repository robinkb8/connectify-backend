# authentication/views.py
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .serializers import UserRegistrationSerializer
from .models import User

@api_view(['POST'])
def register_user(request):
    """
    Handle user registration
    
    This view receives POST requests from React frontend
    and creates new users in the database
    """
    
    # Step 1: Get data from React frontend
    data = request.data
    print(f"Received registration data: {data}")
    
    # Step 2: Validate data using our serializer
    serializer = UserRegistrationSerializer(data=data)
    
    if serializer.is_valid():
        # Step 3: Data is valid, create the user
        try:
            user = serializer.save()
            
            # Step 4: Return success response to React
            return Response({
                'success': True,
                'message': 'Account created successfully!',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'full_name': user.full_name
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Handle any database errors
            return Response({
                'success': False,
                'message': f'Failed to create account: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    else:
        # Step 5: Data is invalid, return errors to React
        return Response({
            'success': False,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_user(request):
    """
    Handle user login
    
    This view authenticates users and returns login status
    """
    
    # Step 1: Get email and password from React
    email = request.data.get('email')
    password = request.data.get('password')
    
    # Step 2: Validate required fields
    if not email or not password:
        return Response({
            'success': False,
            'message': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Step 3: Try to authenticate user
    try:
        # Check if user exists
        user = User.objects.get(email=email)
        
        # Verify password
        if user.check_password(password):
            # Step 4: Login successful
            return Response({
                'success': True,
                'message': 'Login successful!',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'full_name': user.full_name
                }
            }, status=status.HTTP_200_OK)
        else:
            # Wrong password
            return Response({
                'success': False,
                'message': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except User.DoesNotExist:
        # User not found
        return Response({
            'success': False,
            'message': 'Invalid email or password'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    except Exception as e:
        # Handle unexpected errors
        return Response({
            'success': False,
            'message': f'Login failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def check_username_availability(request):
    """
    Check if username is available
    
    This is called when user types in username field
    for real-time validation
    """
    
    username = request.data.get('username', '').strip().lower()
    
    if not username:
        return Response({
            'available': False,
            'message': 'Username is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if username already exists
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
def check_email_availability(request):
    """
    Check if email is available
    
    This is called during registration to check
    if email is already registered
    """
    
    email = request.data.get('email', '').strip().lower()
    
    if not email:
        return Response({
            'available': False,
            'message': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response({
            'available': False,
            'message': 'Email is already registered'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'available': True,
        'message': 'Email is available!'
    }, status=status.HTTP_200_OK)