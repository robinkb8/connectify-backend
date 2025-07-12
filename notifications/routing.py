from django.urls import path
from . import consumers

# WebSocket URL patterns for notifications
websocket_urlpatterns = [
    # WebSocket connection for real-time notifications
    # ws://localhost:8000/ws/notifications/?token={jwt_token}
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi(), name='notification_websocket'),
]