import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs

from .models import Notification
from .serializers import NotificationSerializer

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications
    Handles notification delivery and read status updates
    """

    async def connect(self):
        """Handle WebSocket connection for notifications"""
        # Authenticate user from query parameters
        user = await self.get_user_from_token()
        if not user:
            await self.close(code=4001)  # Unauthorized
            return
        
        self.user = user
        self.notification_group_name = f'notifications_{user.id}'
        
        # Join notification group for this user
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        # Accept WebSocket connection
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to notifications',
            'user_id': self.user.id
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'mark_read':
                await self.handle_mark_read(text_data_json)
            elif message_type == 'mark_all_read':
                await self.handle_mark_all_read(text_data_json)
            elif message_type == 'get_unread_count':
                await self.handle_get_unread_count(text_data_json)
            else:
                await self.send_error('Unknown message type')
                
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON format')
        except Exception as e:
            await self.send_error(f'Error processing message: {str(e)}')

    async def handle_mark_read(self, data):
        """Handle mark notification as read"""
        try:
            notification_id = data.get('notification_id')
            if not notification_id:
                await self.send_error('Notification ID is required')
                return
            
            success = await self.mark_notification_read(notification_id)
            
            if success:
                await self.send(text_data=json.dumps({
                    'type': 'mark_read_success',
                    'notification_id': notification_id,
                    'message': 'Notification marked as read'
                }))
            else:
                await self.send_error('Failed to mark notification as read')
                
        except Exception as e:
            await self.send_error(f'Error marking as read: {str(e)}')

    async def handle_mark_all_read(self, data):
        """Handle mark all notifications as read"""
        try:
            updated_count = await self.mark_all_notifications_read()
            
            await self.send(text_data=json.dumps({
                'type': 'mark_all_read_success',
                'updated_count': updated_count,
                'message': f'Marked {updated_count} notifications as read'
            }))
                
        except Exception as e:
            await self.send_error(f'Error marking all as read: {str(e)}')

    async def handle_get_unread_count(self, data):
        """Handle get unread count request"""
        try:
            count = await self.get_unread_count()
            
            await self.send(text_data=json.dumps({
                'type': 'unread_count',
                'count': count
            }))
                
        except Exception as e:
            await self.send_error(f'Error getting unread count: {str(e)}')

    # Group message handlers
    async def notification_created(self, event):
        """Send new notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': event['notification_data']
        }))

    async def notification_updated(self, event):
        """Send notification update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification_updated',
            'notification_id': event['notification_id'],
            'is_read': event['is_read']
        }))

    async def unread_count_updated(self, event):
        """Send updated unread count to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'unread_count_updated',
            'count': event['count']
        }))

    # Database operations
    @database_sync_to_async
    def get_user_from_token(self):
        """Authenticate user from JWT token in query parameters"""
        try:
            # Get token from query parameters
            query_string = self.scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]
            
            if not token:
                return None
            
            # Validate JWT token
            UntypedToken(token)
            
            # Get user from token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            user = User.objects.select_related('profile').get(id=user_id)
            return user
            
        except Exception:
            return None

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            
            if not notification.is_read:
                notification.mark_as_read()
                return True
            return False
            
        except Notification.DoesNotExist:
            return False
        except Exception:
            return False

    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Mark all notifications as read"""
        try:
            from django.utils import timezone
            
            updated_count = Notification.objects.filter(
                recipient=self.user,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
            
            return updated_count
            
        except Exception:
            return 0

    @database_sync_to_async
    def get_unread_count(self):
        """Get unread notification count"""
        try:
            return Notification.objects.filter(
                recipient=self.user,
                is_read=False
            ).count()
            
        except Exception:
            return 0

    @database_sync_to_async
    def serialize_notification(self, notification):
        """Serialize notification for JSON response"""
        try:
            # Create a mock request for serializer context
            class MockRequest:
                def __init__(self, user):
                    self.user = user
                
                def build_absolute_uri(self, url):
                    return url
            
            mock_request = MockRequest(self.user)
            serializer = NotificationSerializer(
                notification, 
                context={'request': mock_request}
            )
            
            return serializer.data
            
        except Exception as e:
            return {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'error': f'Serialization error: {str(e)}'
            }

    async def send_error(self, error_message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message
        }))