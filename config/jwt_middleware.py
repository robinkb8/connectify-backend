# backend/config/jwt_middleware.py - JWT WebSocket Authentication Middleware
"""
SURGICAL FIX: Custom JWT WebSocket Authentication Middleware

This middleware resolves the AuthMiddlewareStack conflict by providing
JWT token authentication for WebSocket connections while maintaining
session-based authentication for regular HTTP requests.

PROBLEM SOLVED: WebSocket connections closing after handshake due to
AuthMiddlewareStack expecting session auth instead of JWT tokens.
"""

from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT Authentication Middleware for WebSocket connections
    
    Authenticates users via JWT tokens passed in query parameters.
    Falls back to AnonymousUser for invalid/missing tokens.
    """

    def __init__(self, inner):
        """Initialize middleware"""
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        """
        Authenticate WebSocket connection using JWT token
        
        Expected URL format: ws://localhost:8000/ws/chat/{chat_id}/?token={jwt_token}
        """
        # Only process WebSocket connections
        if scope['type'] != 'websocket':
            return await super().__call__(scope, receive, send)

        try:
            # Extract JWT token from query parameters
            query_string = scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]

            if token:
                # Authenticate user using JWT token
                user = await self.get_user_from_jwt_token(token)
                if user:
                    logger.info(f"✅ JWT WebSocket authentication successful for user: {user.username}")
                    scope['user'] = user
                else:
                    logger.warning("❌ JWT WebSocket authentication failed: Invalid token")
                    scope['user'] = AnonymousUser()
            else:
                logger.warning("❌ JWT WebSocket authentication failed: No token provided")
                scope['user'] = AnonymousUser()

        except Exception as e:
            logger.error(f"❌ JWT WebSocket authentication error: {str(e)}")
            scope['user'] = AnonymousUser()

        # Continue to the next middleware/consumer
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_from_jwt_token(self, token):
        """
        Validate JWT token and return authenticated user
        
        Args:
            token (str): JWT access token
            
        Returns:
            User: Authenticated user object or None if invalid
        """
        try:
            # Validate and decode JWT token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # Get user from database
            user = User.objects.select_related('profile').get(id=user_id)
            
            # Verify user is active
            if not user.is_active:
                logger.warning(f"❌ JWT authentication failed: Inactive user {user.username}")
                return None
                
            return user
            
        except (InvalidToken, TokenError) as e:
            logger.warning(f"❌ JWT token validation failed: {str(e)}")
            return None
        except User.DoesNotExist:
            logger.warning(f"❌ JWT authentication failed: User not found for token")
            return None
        except Exception as e:
            logger.error(f"❌ JWT authentication error: {str(e)}")
            return None


def JWTAuthMiddlewareStack(inner):
    """
    JWT Authentication Middleware Stack for WebSocket connections
    
    This replaces Django's AuthMiddlewareStack for WebSocket connections
    that use JWT authentication instead of session-based authentication.
    
    Usage in ASGI configuration:
        "websocket": JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    """
    return JWTAuthMiddleware(inner)


# Alternative: Hybrid middleware that supports both JWT and session auth
class HybridAuthMiddleware(BaseMiddleware):
    """
    Hybrid Authentication Middleware for WebSocket connections
    
    Supports both JWT tokens (query params) and session-based authentication.
    Tries JWT first, falls back to session auth if no token provided.
    """

    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'websocket':
            return await super().__call__(scope, receive, send)

        try:
            # Try JWT authentication first
            query_string = scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]

            if token:
                # Use JWT authentication
                user = await self.get_user_from_jwt_token(token)
                if user:
                    logger.info(f"✅ JWT WebSocket authentication successful for user: {user.username}")
                    scope['user'] = user
                else:
                    logger.warning("❌ JWT WebSocket authentication failed: Invalid token")
                    scope['user'] = AnonymousUser()
            else:
                # Fall back to session authentication
                logger.info("🔄 No JWT token provided, attempting session authentication")
                # Import Django's auth middleware for session handling
                from channels.auth import AuthMiddleware
                auth_middleware = AuthMiddleware(self.inner)
                return await auth_middleware(scope, receive, send)

        except Exception as e:
            logger.error(f"❌ Hybrid WebSocket authentication error: {str(e)}")
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_from_jwt_token(self, token):
        """Same JWT validation as JWTAuthMiddleware"""
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.select_related('profile').get(id=user_id)
            
            if not user.is_active:
                return None
                
            return user
            
        except (InvalidToken, TokenError, User.DoesNotExist):
            return None
        except Exception:
            return None


def HybridAuthMiddlewareStack(inner):
    """
    Hybrid Authentication Middleware Stack
    
    Supports both JWT and session authentication for maximum compatibility.
    """
    return HybridAuthMiddleware(inner)