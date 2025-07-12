# messaging/consumers.py - SAFE WORKING VERSION (ROLLBACK)
import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import UntypedToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs

from .models import Chat, Message, MessageStatus
from .serializers import MessageSerializer

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    SAFE VERSION: WebSocket consumer for real-time chat functionality
    Simplified logic to ensure stable connections
    """

    async def connect(self):
        """Handle WebSocket connection"""
        # Get chat ID from URL
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'
        
        # Authenticate user from query parameters
        user = await self.get_user_from_token()
        if not user:
            await self.close(code=4001)  # Unauthorized
            return
        
        self.user = user
        
        # Verify user is participant in chat
        chat_participant = await self.verify_chat_participant()
        if not chat_participant:
            await self.close(code=4003)  # Forbidden
            return
        
        # Join chat group
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        
        # Accept WebSocket connection
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to chat',
            'chat_id': str(self.chat_id),
            'user_id': self.user.id
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave chat group
        if hasattr(self, 'chat_group_name'):
            await self.channel_layer.group_discard(
                self.chat_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'message_read':
                await self.handle_message_read(text_data_json)
            elif message_type == 'message_delivered':
                await self.handle_message_delivered(text_data_json)
            elif message_type == 'typing_start':
                await self.handle_typing_start(text_data_json)
            elif message_type == 'typing_stop':
                await self.handle_typing_stop(text_data_json)
            else:
                await self.send_error('Unknown message type')
                
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON format')
        except Exception as e:
            await self.send_error(f'Error processing message: {str(e)}')

    async def handle_chat_message(self, data):
        """Handle new chat message"""
        try:
            content = data.get('content', '').strip()
            reply_to_id = data.get('reply_to')
            
            if not content:
                await self.send_error('Message content cannot be empty')
                return
            
            # Create message in database
            message = await self.create_message(content, reply_to_id)
            
            # Serialize message for sending
            message_data = await self.serialize_message(message)
            
            # Send message to chat group
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_message_broadcast',
                    'message_data': message_data
                }
            )
            
        except Exception as e:
            await self.send_error(f'Error sending message: {str(e)}')

    async def handle_message_read(self, data):
        """Handle message read status update"""
        try:
            message_id = data.get('message_id')
            if not message_id:
                await self.send_error('Message ID is required')
                return
            
            # Update message status
            success = await self.mark_message_read(message_id)
            
            if success:
                # Broadcast read status to chat group
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        'type': 'message_status_update',
                        'message_id': message_id,
                        'status': 'read',
                        'user_id': self.user.id,
                        'timestamp': timezone.now().isoformat()
                    }
                )
            else:
                await self.send_error('Failed to mark message as read')
                
        except Exception as e:
            await self.send_error(f'Error updating read status: {str(e)}')

    async def handle_message_delivered(self, data):
        """Handle message delivered status update"""
        try:
            message_id = data.get('message_id')
            if not message_id:
                await self.send_error('Message ID is required')
                return
            
            # Update message status
            success = await self.mark_message_delivered(message_id)
            
            if success:
                # Broadcast delivered status to chat group
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        'type': 'message_status_update',
                        'message_id': message_id,
                        'status': 'delivered',
                        'user_id': self.user.id,
                        'timestamp': timezone.now().isoformat()
                    }
                )
                
        except Exception as e:
            await self.send_error(f'Error updating delivered status: {str(e)}')

    async def handle_typing_start(self, data):
        """Handle typing indicator start"""
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': True
            }
        )

    async def handle_typing_stop(self, data):
        """Handle typing indicator stop"""
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': False
            }
        )

    # Group message handlers
    async def chat_message_broadcast(self, event):
        """Send message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message_data']
        }))

    async def message_status_update(self, event):
        """Send message status update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message_status',
            'message_id': event['message_id'],
            'status': event['status'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send typing indicator to the user who is typing
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
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
            
            # Get user (basic version without complex select_related)
            user = User.objects.get(id=user_id)
            return user
            
        except Exception:
            return None

    @database_sync_to_async
    def verify_chat_participant(self):
        """Verify user is participant in the chat"""
        try:
            return Chat.objects.filter(
                id=self.chat_id,
                participants=self.user
            ).exists()
        except:
            return False

    @database_sync_to_async
    def create_message(self, content, reply_to_id=None):
        """Create new message in database"""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            
            # Get reply_to message if specified
            reply_to = None
            if reply_to_id:
                try:
                    reply_to = Message.objects.get(
                        id=reply_to_id,
                        chat=chat
                    )
                except Message.DoesNotExist:
                    pass
            
            # Create message
            message = Message.objects.create(
                chat=chat,
                sender=self.user,
                content=content,
                message_type='text',
                reply_to=reply_to
            )
            
            return message
            
        except Exception as e:
            raise Exception(f'Failed to create message: {str(e)}')

    @database_sync_to_async
    def serialize_message(self, message):
        """SAFE VERSION: Basic message serialization"""
        try:
            # Get message with basic related data
            message = Message.objects.select_related(
                'sender',
                'reply_to',
                'reply_to__sender'
            ).get(id=message.id)
            
            # Create a basic mock request for serializer context
            class MockRequest:
                def __init__(self, user):
                    self.user = user
                
                def build_absolute_uri(self, url):
                    return url
            
            mock_request = MockRequest(self.user)
            serializer = MessageSerializer(
                message, 
                context={'request': mock_request}
            )
            
            return serializer.data
            
        except Exception as e:
            # Fallback for any serialization errors
            return {
                'id': str(message.id),
                'content': message.content,
                'sender': {
                    'id': message.sender.id,
                    'username': message.sender.username,
                    'full_name': getattr(message.sender, 'full_name', message.sender.username)
                },
                'created_at': message.created_at.isoformat(),
                'error': f'Serialization fallback: {str(e)}'
            }

    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark message as read"""
        try:
            message = Message.objects.get(
                id=message_id,
                chat__participants=self.user
            )
            
            # Don't mark own messages as read
            if message.sender == self.user:
                return False
            
            # Get or create message status
            status_record, created = MessageStatus.objects.get_or_create(
                message=message,
                user=self.user
            )
            
            # Mark as read
            status_record.mark_read()
            return True
            
        except Message.DoesNotExist:
            return False
        except Exception:
            return False

    @database_sync_to_async
    def mark_message_delivered(self, message_id):
        """Mark message as delivered"""
        try:
            message = Message.objects.get(
                id=message_id,
                chat__participants=self.user
            )
            
            # Don't mark own messages as delivered
            if message.sender == self.user:
                return False
            
            # Get or create message status
            status_record, created = MessageStatus.objects.get_or_create(
                message=message,
                user=self.user
            )
            
            # Mark as delivered
            status_record.mark_delivered()
            return True
            
        except Message.DoesNotExist:
            return False
        except Exception:
            return False

    async def send_error(self, error_message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message
        }))