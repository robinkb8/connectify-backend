# authentication/views.py - CHANGE 4: Add Followers/Following Lists
# ALL EXISTING FUNCTIONS PRESERVED - ADDING 2 NEW LIST ENDPOINTS

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator

from .serializers import UserRegistrationSerializer
from .models import User, EmailOTP
from .email_service import generate_otp, send_otp_email

# ===== ALL EXISTING FUNCTIONS PRESERVED EXACTLY AS-IS =====
# (Including all functions from Changes 1, 2, and 3)

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
    """Handle user registration with JWT token generation and profile creation"""
    data = request.data
    serializer = UserRegistrationSerializer(data=data)
    
    if serializer.is_valid():
        try:
            user = serializer.save()
            
            # Ensure profile exists (signal should create it, but just in case)
            from core.models import UserProfile
            if not hasattr(user, 'profile'):
                UserProfile.objects.get_or_create(user=user)
            
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
                    'full_name': user.full_name,
                    'profile': {
                        'bio': user.profile.bio,
                        'avatar': user.profile.avatar.url if user.profile.avatar else None,
                        'website': user.profile.website,
                        'location': user.profile.location,
                        'is_private': user.profile.is_private,
                        'followers_count': user.profile.followers_count,
                        'following_count': user.profile.following_count,
                        'posts_count': user.profile.posts_count,
                    }
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
    """Handle user login with JWT token generation and profile data"""
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
            # Ensure profile exists
            from core.models import UserProfile
            if not hasattr(user, 'profile'):
                UserProfile.objects.get_or_create(user=user)
            
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
                    'full_name': user.full_name,
                    'profile': {
                        'bio': user.profile.bio,
                        'avatar': user.profile.avatar.url if user.profile.avatar else None,
                        'website': user.profile.website,
                        'location': user.profile.location,
                        'is_private': user.profile.is_private,
                        'followers_count': user.profile.followers_count,
                        'following_count': user.profile.following_count,
                        'posts_count': user.profile.posts_count,
                    }
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
    """Get current authenticated user info with profile"""
    user = request.user
    
    # Ensure profile exists
    from core.models import UserProfile
    if not hasattr(user, 'profile'):
        UserProfile.objects.get_or_create(user=user)
    
    return Response({
        'success': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'full_name': user.full_name,
            'profile': {
                'bio': user.profile.bio,
                'avatar': user.profile.avatar.url if user.profile.avatar else None,
                'website': user.profile.website,
                'location': user.profile.location,
                'is_private': user.profile.is_private,
                'followers_count': user.profile.followers_count,
                'following_count': user.profile.following_count,
                'posts_count': user.profile.posts_count,
            }
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_avatar(request):
    """Upload user avatar"""
    if 'avatar' not in request.FILES:
        return Response({
            'success': False,
            'message': 'No avatar file provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    
    # Ensure profile exists
    from core.models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Update avatar
    profile.avatar = request.FILES['avatar']
    profile.save()
    
    return Response({
        'success': True,
        'message': 'Avatar uploaded successfully',
        'avatar_url': profile.avatar.url if profile.avatar else None
    })


@api_view(['GET'])
@permission_classes([])
def get_user_profile(request, username):
    """
    GET /api/users/{username}/ - Get any user's profile by username
    
    NEW ENDPOINT for viewing other users' profiles
    Public endpoint - no authentication required for public profiles
    """
    try:
        # Find user by username (case-insensitive)
        user = get_object_or_404(User, username__iexact=username)
        
        # Ensure profile exists
        from core.models import UserProfile
        if not hasattr(user, 'profile'):
            UserProfile.objects.get_or_create(user=user)
        
        # Check if profile is private and user is not authenticated
        if user.profile.is_private and not request.user.is_authenticated:
            return Response({
                'success': False,
                'message': 'This profile is private'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if current user is viewing their own profile
        is_own_profile = request.user.is_authenticated and request.user.id == user.id
        
        # For private profiles, only allow owner and followers to view
        if user.profile.is_private and not is_own_profile:
            # Check if current user follows this user
            from core.models import Follow
            is_following = request.user.is_authenticated and Follow.objects.filter(
                follower=request.user, 
                following=user
            ).exists()
            
            if not is_following:
                return Response({
                    'success': False,
                    'message': 'This profile is private. Follow to see their content.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Determine follow status if user is authenticated
        is_following = False
        if request.user.is_authenticated and not is_own_profile:
            from core.models import Follow
            is_following = Follow.objects.filter(
                follower=request.user,
                following=user
            ).exists()
        
        # Return profile data
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email if is_own_profile else None,  # Hide email for others
                'date_joined': user.date_joined.isoformat(),
                'profile': {
                    'bio': user.profile.bio,
                    'avatar': user.profile.avatar.url if user.profile.avatar else None,
                    'website': user.profile.website,
                    'location': user.profile.location,
                    'is_private': user.profile.is_private,
                    'followers_count': user.profile.followers_count,
                    'following_count': user.profile.following_count,
                    'posts_count': user.profile.posts_count,
                },
                'is_own_profile': is_own_profile,
                'is_following': is_following,
            }
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching profile: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request, user_id):
    """
    POST /api/auth/users/{user_id}/follow/ - Follow a user
    
    NEW ENDPOINT for following users
    """
    try:
        # Get the user to follow
        user_to_follow = get_object_or_404(User, id=user_id)
        current_user = request.user
        
        # Prevent users from following themselves
        if current_user.id == user_to_follow.id:
            return Response({
                'success': False,
                'message': 'You cannot follow yourself'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already following
        from core.models import Follow, UserProfile
        
        # Ensure both users have profiles
        UserProfile.objects.get_or_create(user=current_user)
        UserProfile.objects.get_or_create(user=user_to_follow)
        
        existing_follow = Follow.objects.filter(
            follower=current_user,
            following=user_to_follow
        ).first()
        
        if existing_follow:
            return Response({
                'success': False,
                'message': 'You are already following this user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create follow relationship with atomic transaction
        with transaction.atomic():
            # Create the follow relationship
            Follow.objects.create(
                follower=current_user,
                following=user_to_follow
            )
            
            # Update follower counts
            current_user.profile.following_count = Follow.objects.filter(follower=current_user).count()
            user_to_follow.profile.followers_count = Follow.objects.filter(following=user_to_follow).count()
            
            current_user.profile.save(update_fields=['following_count'])
            user_to_follow.profile.save(update_fields=['followers_count'])
        
        return Response({
            'success': True,
            'message': f'You are now following {user_to_follow.full_name}',
            'is_following': True,
            'follower_count': user_to_follow.profile.followers_count,
            'following_count': current_user.profile.following_count,
        }, status=status.HTTP_201_CREATED)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error following user: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unfollow_user(request, user_id):
    """
    DELETE /api/auth/users/{user_id}/follow/ - Unfollow a user
    
    NEW ENDPOINT for unfollowing users
    """
    try:
        # Get the user to unfollow
        user_to_unfollow = get_object_or_404(User, id=user_id)
        current_user = request.user
        
        # Prevent users from unfollowing themselves
        if current_user.id == user_to_unfollow.id:
            return Response({
                'success': False,
                'message': 'You cannot unfollow yourself'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if actually following
        from core.models import Follow, UserProfile
        
        # Ensure both users have profiles
        UserProfile.objects.get_or_create(user=current_user)
        UserProfile.objects.get_or_create(user=user_to_unfollow)
        
        follow_relationship = Follow.objects.filter(
            follower=current_user,
            following=user_to_unfollow
        ).first()
        
        if not follow_relationship:
            return Response({
                'success': False,
                'message': 'You are not following this user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove follow relationship with atomic transaction
        with transaction.atomic():
            # Delete the follow relationship
            follow_relationship.delete()
            
            # Update follower counts
            current_user.profile.following_count = Follow.objects.filter(follower=current_user).count()
            user_to_unfollow.profile.followers_count = Follow.objects.filter(following=user_to_unfollow).count()
            
            current_user.profile.save(update_fields=['following_count'])
            user_to_unfollow.profile.save(update_fields=['followers_count'])
        
        return Response({
            'success': True,
            'message': f'You have unfollowed {user_to_unfollow.full_name}',
            'is_following': False,
            'follower_count': user_to_unfollow.profile.followers_count,
            'following_count': current_user.profile.following_count,
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error unfollowing user: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """
    Enhanced profile update with comprehensive validation and field handling
    
    ENHANCED VERSION - supports more fields with better validation
    """
    try:
        user = request.user
        
        # Ensure profile exists
        from core.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Dictionary to track what was updated
        updated_fields = []
        validation_errors = {}
        
        # Bio validation and update
        if 'bio' in request.data:
            bio = request.data.get('bio', '').strip()
            if len(bio) > 150:
                validation_errors['bio'] = 'Bio must be 150 characters or less'
            else:
                profile.bio = bio
                updated_fields.append('bio')
        
        # Website validation and update
        if 'website' in request.data:
            website = request.data.get('website', '').strip()
            if website:
                # Add protocol if missing
                if not website.startswith(('http://', 'https://')):
                    website = 'https://' + website
                
                # Validate URL format
                try:
                    validator = URLValidator()
                    validator(website)
                    profile.website = website
                    updated_fields.append('website')
                except ValidationError:
                    validation_errors['website'] = 'Please enter a valid website URL'
            else:
                profile.website = ''
                updated_fields.append('website')
        
        # Location validation and update
        if 'location' in request.data:
            location = request.data.get('location', '').strip()
            if len(location) > 50:
                validation_errors['location'] = 'Location must be 50 characters or less'
            else:
                profile.location = location
                updated_fields.append('location')
        
        # Privacy setting update
        if 'is_private' in request.data:
            is_private = request.data.get('is_private')
            if isinstance(is_private, bool):
                profile.is_private = is_private
                updated_fields.append('is_private')
            else:
                validation_errors['is_private'] = 'Privacy setting must be true or false'
        
        # Full name validation and update (optional enhancement)
        if 'full_name' in request.data:
            full_name = request.data.get('full_name', '').strip()
            if not full_name:
                validation_errors['full_name'] = 'Full name cannot be empty'
            elif len(full_name) > 50:
                validation_errors['full_name'] = 'Full name must be 50 characters or less'
            else:
                user.full_name = full_name
                updated_fields.append('full_name')
        
        # Username validation and update (careful - must be unique)
        if 'username' in request.data:
            new_username = request.data.get('username', '').strip().lower()
            if not new_username:
                validation_errors['username'] = 'Username cannot be empty'
            elif len(new_username) < 3:
                validation_errors['username'] = 'Username must be at least 3 characters'
            elif len(new_username) > 30:
                validation_errors['username'] = 'Username must be 30 characters or less'
            elif not new_username.replace('_', '').replace('.', '').isalnum():
                validation_errors['username'] = 'Username can only contain letters, numbers, dots, and underscores'
            elif new_username != user.username:
                # Check if username is already taken
                if User.objects.filter(username=new_username).exists():
                    validation_errors['username'] = 'This username is already taken'
                else:
                    user.username = new_username
                    updated_fields.append('username')
        
        # Handle avatar upload
        if 'avatar' in request.FILES:
            avatar_file = request.FILES['avatar']
            
            # Validate file size (max 5MB)
            if avatar_file.size > 5 * 1024 * 1024:
                validation_errors['avatar'] = 'Avatar file must be smaller than 5MB'
            # Validate file type
            elif not avatar_file.content_type.startswith('image/'):
                validation_errors['avatar'] = 'Avatar must be an image file'
            else:
                profile.avatar = avatar_file
                updated_fields.append('avatar')
        
        # If there are validation errors, return them
        if validation_errors:
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': validation_errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save changes with atomic transaction
        with transaction.atomic():
            if 'full_name' in updated_fields or 'username' in updated_fields:
                user.save()
            
            if any(field in updated_fields for field in ['bio', 'website', 'location', 'is_private', 'avatar']):
                profile.save()
        
        # Prepare response data
        response_data = {
            'success': True,
            'message': f"Profile updated successfully ({', '.join(updated_fields)})" if updated_fields else "No changes made",
            'updated_fields': updated_fields,
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'profile': {
                    'bio': profile.bio,
                    'avatar': profile.avatar.url if profile.avatar else None,
                    'website': profile.website,
                    'location': profile.location,
                    'is_private': profile.is_private,
                    'followers_count': profile.followers_count,
                    'following_count': profile.following_count,
                    'posts_count': profile.posts_count,
                }
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error updating profile: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===== NEW FUNCTIONS - CHANGE 4: FOLLOWERS/FOLLOWING LISTS =====

@api_view(['GET'])
@permission_classes([])
def get_user_followers(request, user_id):
    """
    GET /api/auth/users/{user_id}/followers/ - Get list of users who follow this user
    
    NEW ENDPOINT for getting followers list with pagination
    """
    try:
        # Get the target user
        target_user = get_object_or_404(User, id=user_id)
        
        # Ensure profile exists
        from core.models import UserProfile, Follow
        UserProfile.objects.get_or_create(user=target_user)
        
        # Check if profile is private
        if target_user.profile.is_private:
            # Only allow owner and followers to see followers list
            if not request.user.is_authenticated:
                return Response({
                    'success': False,
                    'message': 'This profile is private'
                }, status=status.HTTP_403_FORBIDDEN)
            
            is_owner = request.user.id == target_user.id
            is_following = Follow.objects.filter(
                follower=request.user,
                following=target_user
            ).exists()
            
            if not is_owner and not is_following:
                return Response({
                    'success': False,
                    'message': 'This profile is private. Follow to see their followers.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 50)  # Max 50 per page
        
        # Get followers with user profile data
        followers_queryset = Follow.objects.filter(
            following=target_user
        ).select_related(
            'follower',
            'follower__profile'
        ).order_by('-created_at')
        
        # Paginate results
        paginator = Paginator(followers_queryset, page_size)
        followers_page = paginator.get_page(page)
        
        # Format follower data
        followers_data = []
        for follow in followers_page:
            follower = follow.follower
            
            # Ensure follower has profile
            if not hasattr(follower, 'profile'):
                UserProfile.objects.get_or_create(user=follower)
            
            # Check if current user follows this follower
            current_user_follows = False
            if request.user.is_authenticated and request.user.id != follower.id:
                current_user_follows = Follow.objects.filter(
                    follower=request.user,
                    following=follower
                ).exists()
            
            followers_data.append({
                'id': follower.id,
                'username': follower.username,
                'full_name': follower.full_name,
                'profile': {
                    'avatar': follower.profile.avatar.url if follower.profile.avatar else None,
                    'bio': follower.profile.bio,
                    'followers_count': follower.profile.followers_count,
                    'is_private': follower.profile.is_private,
                },
                'is_following': current_user_follows,
                'followed_at': follow.created_at.isoformat(),
            })
        
        return Response({
            'success': True,
            'user': {
                'id': target_user.id,
                'username': target_user.username,
                'full_name': target_user.full_name,
            },
            'followers': followers_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': followers_page.has_next(),
                'has_previous': followers_page.has_previous(),
            }
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except ValueError:
        return Response({
            'success': False,
            'message': 'Invalid page or page_size parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching followers: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([])
def get_user_following(request, user_id):
    """
    GET /api/auth/users/{user_id}/following/ - Get list of users this user follows
    
    NEW ENDPOINT for getting following list with pagination
    """
    try:
        # Get the target user
        target_user = get_object_or_404(User, id=user_id)
        
        # Ensure profile exists
        from core.models import UserProfile, Follow
        UserProfile.objects.get_or_create(user=target_user)
        
        # Check if profile is private
        if target_user.profile.is_private:
            # Only allow owner and followers to see following list
            if not request.user.is_authenticated:
                return Response({
                    'success': False,
                    'message': 'This profile is private'
                }, status=status.HTTP_403_FORBIDDEN)
            
            is_owner = request.user.id == target_user.id
            is_following = Follow.objects.filter(
                follower=request.user,
                following=target_user
            ).exists()
            
            if not is_owner and not is_following:
                return Response({
                    'success': False,
                    'message': 'This profile is private. Follow to see who they follow.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 50)  # Max 50 per page
        
        # Get following with user profile data
        following_queryset = Follow.objects.filter(
            follower=target_user
        ).select_related(
            'following',
            'following__profile'
        ).order_by('-created_at')
        
        # Paginate results
        paginator = Paginator(following_queryset, page_size)
        following_page = paginator.get_page(page)
        
        # Format following data
        following_data = []
        for follow in following_page:
            following_user = follow.following
            
            # Ensure following user has profile
            if not hasattr(following_user, 'profile'):
                UserProfile.objects.get_or_create(user=following_user)
            
            # Check if current user follows this user
            current_user_follows = False
            if request.user.is_authenticated and request.user.id != following_user.id:
                current_user_follows = Follow.objects.filter(
                    follower=request.user,
                    following=following_user
                ).exists()
            
            following_data.append({
                'id': following_user.id,
                'username': following_user.username,
                'full_name': following_user.full_name,
                'profile': {
                    'avatar': following_user.profile.avatar.url if following_user.profile.avatar else None,
                    'bio': following_user.profile.bio,
                    'followers_count': following_user.profile.followers_count,
                    'is_private': following_user.profile.is_private,
                },
                'is_following': current_user_follows,
                'followed_at': follow.created_at.isoformat(),
            })
        
        return Response({
            'success': True,
            'user': {
                'id': target_user.id,
                'username': target_user.username,
                'full_name': target_user.full_name,
            },
            'following': following_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': following_page.has_next(),
                'has_previous': following_page.has_previous(),
            }
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except ValueError:
        return Response({
            'success': False,
            'message': 'Invalid page or page_size parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching following: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)