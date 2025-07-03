# messaging/routing.py - COMPLETE WEBSOCKET ROUTING
from django.urls import re_path, path
from . import consumers

# WebSocket URL patterns for messaging
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
]