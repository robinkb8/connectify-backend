# messaging/routing.py - COMPLETE WEBSOCKET ROUTING
from django.urls import re_path, path
from . import consumers

# Import notification consumers
from notifications import consumers as notification_consumers

# WebSocket URL patterns for messaging and notifications
websocket_urlpatterns = [
    # WebSocket connection for real-time chat
    # ws://localhost:8000/ws/chat/{chat_id}/?token={jwt_token}
    re_path(
        r'ws/chat/(?P<chat_id>[0-9a-f-]{36})/$',
        consumers.ChatConsumer.as_asgi(),
        name='chat_websocket'
    ),
    
    # Alternative path pattern (more explicit)
    path(
        'ws/chat/<uuid:chat_id>/',
        consumers.ChatConsumer.as_asgi(),
        name='chat_websocket_alt'
    ),
    
    # WebSocket connection for real-time notifications
    # ws://localhost:8000/ws/notifications/?token={jwt_token}
    path(
        'ws/notifications/',
        notification_consumers.NotificationConsumer.as_asgi(),
        name='notification_websocket'
    ),
]