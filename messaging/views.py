# messaging/views.py - MINIMAL WORKING VERSION (Resolves URLconf Error)
"""
MINIMAL working messaging views that resolve the URLconf error.
This version focuses on getting the server running first, then we can add optimizations.

FUNCTIONALITY PRESERVED:
- All existing endpoints work identically
- All URL patterns match exactly
- All response formats unchanged
- All validation logic maintained
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Max, Prefetch, F
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Chat, Message, MessageStatus
from .serializers import (
    ChatSerializer,
    ChatCreateSerializer, 
    ChatDetailSerializer,
    MessageSerializer,
    MessageCreateSerializer,
    ChatParticipantSerializer
)

User = get_user_model()


class ChatListCreateAPIView(generics.ListCreateAPIView):
    """
    💬 CHAT MANAGEMENT - List and Create Chats
    GET /api/messaging/chats/ - List user's chats
    POST /api/messaging/chats/ - Create new chat
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ChatCreateSerializer
        return ChatSerializer
    
    def get_queryset(self):
        """Basic optimized query for user's chats"""
        user = self.request.user
        
        return Chat.objects.filter(
            participants=user
        ).select_related(
            'last_message',
            'last_message__sender'
        ).prefetch_related(
            'participants'
        ).order_by('-last_activity')
    
    def create(self, request, *args, **kwargs):
        """Handle chat creation"""
        serializer = ChatCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        chat = self.perform_create(serializer)
        output_serializer = ChatSerializer(chat, context={'request': request})
        
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        """Create chat and handle duplicates"""
        chat = serializer.save()
        
        if not chat.is_group_chat:
            other_participant = chat.participants.exclude(id=self.request.user.id).first()
            
            existing_chat = Chat.objects.filter(
                is_group_chat=False,
                participants=self.request.user
            ).filter(
                participants=other_participant
            ).exclude(id=chat.id).first()
            
            if existing_chat:
                chat.delete()
                return existing_chat
        
        return chat


class ChatDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    💬 CHAT DETAIL - Get, Update, Delete Chat
    GET /api/messaging/chats/{id}/ - Get chat details
    PUT /api/messaging/chats/{id}/ - Update chat
    DELETE /api/messaging/chats/{id}/ - Delete/leave chat
    """
    serializer_class = ChatDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        """Basic query for chat details"""
        return Chat.objects.filter(
            participants=self.request.user
        ).select_related(
            'last_message',
            'last_message__sender'
        ).prefetch_related(
            'participants'
        )
    
    def perform_update(self, serializer):
        """Update chat (group chats only)"""
        chat = self.get_object()
        
        if chat.is_group_chat:
            serializer.save()
        else:
            return Response({
                'success': False,
                'message': 'Cannot update direct message chats'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_destroy(self, instance):
        """Leave or delete chat"""
        user = self.request.user
        
        instance.participants.remove(user)
        
        if instance.participants.count() == 0:
            instance.delete()
        else:
            instance.last_activity = timezone.now()
            instance.save()


class ChatMessagesListCreateAPIView(generics.ListCreateAPIView):
    """
    📨 MESSAGE MANAGEMENT - List and Send Messages
    GET /api/messaging/chats/{id}/messages/ - Get messages
    POST /api/messaging/chats/{id}/messages/ - Send message
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer
    
    def get_queryset(self):
        """Basic query for messages"""
        chat_id = self.kwargs['chat_id']
        
        chat = get_object_or_404(
            Chat.objects.filter(participants=self.request.user),
            id=chat_id
        )
        
        return Message.objects.filter(
            chat=chat,
            is_deleted=False
        ).select_related(
            'sender',
            'reply_to',
            'reply_to__sender'
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        """Send new message"""
        chat_id = self.kwargs['chat_id']
        
        chat = get_object_or_404(
            Chat.objects.filter(participants=self.request.user),
            id=chat_id
        )
        
        message = serializer.save(
            chat=chat,
            sender=self.request.user
        )
        
        return message


class MessageDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    📨 MESSAGE DETAIL - Get, Edit, Delete Message
    GET /api/messaging/messages/{id}/ - Get message
    PUT /api/messaging/messages/{id}/ - Edit message
    DELETE /api/messaging/messages/{id}/ - Delete message
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        return Message.objects.filter(
            chat__participants=self.request.user
        ).select_related(
            'sender',
            'chat'
        )
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return MessageCreateSerializer
        return MessageSerializer
    
    def perform_update(self, serializer):
        """Update message (sender only)"""
        message = self.get_object()
        
        if message.sender != self.request.user:
            return Response({
                'success': False,
                'message': 'You can only edit your own messages'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer.save()
        message.mark_as_edited()
    
    def perform_destroy(self, instance):
        """Delete message (sender only)"""
        if instance.sender != self.request.user:
            return Response({
                'success': False,
                'message': 'You can only delete your own messages'
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance.soft_delete()


# MESSAGE STATUS ENDPOINTS - FUNCTION VIEWS

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_message_read(request, message_id):
    """Mark message as read"""
    try:
        message = get_object_or_404(
            Message.objects.filter(chat__participants=request.user),
            id=message_id
        )
        
        if message.sender == request.user:
            return Response({
                'success': False,
                'message': 'Cannot mark your own message as read'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        status_record, created = MessageStatus.objects.get_or_create(
            message=message,
            user=request.user
        )
        
        status_record.mark_read()
        
        return Response({
            'success': True,
            'message': 'Message marked as read',
            'read_at': status_record.read_at
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error marking message as read: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_message_delivered(request, message_id):
    """Mark message as delivered"""
    try:
        message = get_object_or_404(
            Message.objects.filter(chat__participants=request.user),
            id=message_id
        )
        
        if message.sender == request.user:
            return Response({
                'success': False,
                'message': 'Cannot mark your own message as delivered'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        status_record, created = MessageStatus.objects.get_or_create(
            message=message,
            user=request.user
        )
        
        status_record.mark_delivered()
        
        return Response({
            'success': True,
            'message': 'Message marked as delivered',
            'delivered_at': status_record.delivered_at
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error marking message as delivered: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# SEARCH ENDPOINTS

class SearchUsersAPIView(generics.ListAPIView):
    """Search users to start chat with"""
    serializer_class = ChatParticipantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        
        if not query or len(query) < 2:
            return User.objects.none()
        
        return User.objects.exclude(
            id=self.request.user.id
        ).filter(
            Q(username__icontains=query) |
            Q(full_name__icontains=query)
        )[:20]


# PARTICIPANT MANAGEMENT

class ChatParticipantsAPIView(generics.ListAPIView):
    """List chat participants"""
    serializer_class = ChatParticipantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        
        chat = get_object_or_404(
            Chat.objects.filter(participants=self.request.user),
            id=chat_id
        )
        
        return chat.participants.all()


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_chat_participant(request, chat_id, user_id):
    """Add/remove chat participants"""
    try:
        chat = get_object_or_404(
            Chat.objects.filter(participants=request.user),
            id=chat_id
        )
        
        target_user = get_object_or_404(User, id=user_id)
        
        if request.method == 'POST':
            # Add participant
            if not chat.is_group_chat:
                return Response({
                    'success': False,
                    'message': 'Cannot add participants to direct messages'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if chat.participants.filter(id=user_id).exists():
                return Response({
                    'success': False,
                    'message': 'User is already a participant'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            chat.add_participant(target_user)
            
            return Response({
                'success': True,
                'message': f'{target_user.username} added to chat'
            })
            
        elif request.method == 'DELETE':
            # Remove participant
            if not chat.participants.filter(id=user_id).exists():
                return Response({
                    'success': False,
                    'message': 'User is not a participant'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if target_user == request.user:
                return Response({
                    'success': False,
                    'message': 'Use chat delete endpoint to leave chat'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            chat.remove_participant(target_user)
            
            return Response({
                'success': True,
                'message': f'{target_user.username} removed from chat'
            })
            
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error managing participant: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)