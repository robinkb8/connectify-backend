"""
ASGI config for config project - FIXED: JWT WebSocket Authentication

SURGICAL FIX APPLIED: Replaced AuthMiddlewareStack with JWTAuthMiddlewareStack
to resolve WebSocket connection closures caused by JWT/session auth conflict.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

# FIXED: Import custom JWT middleware instead of AuthMiddlewareStack
from .jwt_middleware import JWTAuthMiddlewareStack

# Import WebSocket URL patterns
from messaging.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# FIXED: ASGI application with JWT WebSocket authentication
application = ProtocolTypeRouter({
    # Handle traditional HTTP requests (preserves existing functionality)
    "http": django_asgi_app,
    
    # FIXED: Handle WebSocket connections with JWT authentication
    # This replaces AuthMiddlewareStack which expected session-based auth
    "websocket": JWTAuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})

# DEBUGGING: Alternative hybrid configuration (commented out)
# If you need to support both JWT and session auth, uncomment this:
#
# from .jwt_middleware import HybridAuthMiddlewareStack
# 
# application = ProtocolTypeRouter({
#     "http": django_asgi_app,
#     "websocket": HybridAuthMiddlewareStack(
#         URLRouter(websocket_urlpatterns)
#     ),
# })