# messaging/views.py - COMPLETE MESSAGING API VIEWS (FIXED)
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Max
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
    GET /api/messaging/chats/ - List user's chats
    POST /api/messaging/chats/ - Create new chat
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializer for creation"""
        if self.request.method == 'POST':
            return ChatCreateSerializer
        return ChatSerializer
    
    def get_queryset(self):
        """Get chats for current user, ordered by last activity"""
        user = self.request.user
        
        return Chat.objects.filter(
            participants=user
        ).select_related(
            'last_message',
            'last_message__sender'
        ).prefetch_related(
            'participants',
            'participants__profile'
        ).annotate(
            # Add unread count annotation for optimization
            unread_count=Count(
                'messages__status_records',
                filter=Q(
                    messages__status_records__user=user,
                    messages__status_records__status__in=['sent', 'delivered']
                )
            )
        ).order_by('-last_activity')
    
    def create(self, request, *args, **kwargs):
        """
        FIXED: Handle chat creation with proper response serialization
        Use ChatCreateSerializer for input, ChatSerializer for output
        """
        # Use ChatCreateSerializer for input validation
        serializer = ChatCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Create the chat using existing perform_create logic
        chat = self.perform_create(serializer)
        
        # Use ChatSerializer for output response to include all fields (id, participants, etc.)
        output_serializer = ChatSerializer(chat, context={'request': request})
        
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        """Create chat and handle participant validation"""
        chat = serializer.save()
        
        # Check for existing direct message chat
        if not chat.is_group_chat:
            other_participant = chat.participants.exclude(id=self.request.user.id).first()
            
            # Check if direct chat already exists between these users
            existing_chat = Chat.objects.filter(
                is_group_chat=False,
                participants=self.request.user
            ).filter(
                participants=other_participant
            ).exclude(id=chat.id).first()
            
            if existing_chat:
                # Delete the newly created chat and return existing one
                chat.delete()
                return existing_chat
        
        return chat


class ChatDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/messaging/chats/{id}/ - Get chat details with recent messages
    PUT /api/messaging/chats/{id}/ - Update chat (name, etc.)
    DELETE /api/messaging/chats/{id}/ - Leave/delete chat
    """
    serializer_class = ChatDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        """Get chats user participates in"""
        return Chat.objects.filter(
            participants=self.request.user
        ).select_related(
            'last_message',
            'last_message__sender'
        ).prefetch_related(
            'participants',
            'participants__profile',
            'messages__sender',
            'messages__sender__profile'
        )
    
    def perform_update(self, serializer):
        """Update chat (only group chat names for now)"""
        chat = self.get_object()
        
        # Only allow updating group chat names
        if chat.is_group_chat:
            serializer.save()
        else:
            return Response({
                'success': False,
                'message': 'Cannot update direct message chats'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_destroy(self, instance):
        """Leave chat or delete if last participant"""
        user = self.request.user
        
        # Remove user from chat
        instance.participants.remove(user)
        
        # If no participants left, delete the chat
        if instance.participants.count() == 0:
            instance.delete()
        else:
            # Update last activity
            instance.last_activity = timezone.now()
            instance.save()


class ChatMessagesListCreateAPIView(generics.ListCreateAPIView):
    """
    GET /api/messaging/chats/{id}/messages/ - Get message history (paginated)
    POST /api/messaging/chats/{id}/messages/ - Send new message
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        """Use different serializer for creation"""
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer
    
    def get_queryset(self):
        """Get messages for specific chat"""
        chat_id = self.kwargs['chat_id']
        
        # Verify user is participant in chat
        chat = get_object_or_404(
            Chat.objects.filter(participants=self.request.user),
            id=chat_id
        )
        
        return Message.objects.filter(
            chat=chat,
            is_deleted=False
        ).select_related(
            'sender',
            'sender__profile',
            'reply_to',
            'reply_to__sender'
        ).order_by('-created_at')  # Newest first for pagination
    
    def perform_create(self, serializer):
        """Send new message to chat"""
        chat_id = self.kwargs['chat_id']
        
        # Get chat and verify participation
        chat = get_object_or_404(
            Chat.objects.filter(participants=self.request.user),
            id=chat_id
        )
        
        # Create message
        message = serializer.save(
            chat=chat,
            sender=self.request.user
        )
        
        # Update chat's last activity
        chat.last_activity = timezone.now()
        chat.save(update_fields=['last_activity'])
        
        return message


class MessageDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/messaging/messages/{id}/ - Get message details
    PUT /api/messaging/messages/{id}/ - Edit message (sender only)
    DELETE /api/messaging/messages/{id}/ - Delete message (sender only)
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        """Get messages user can access"""
        # User can access messages from chats they participate in
        return Message.objects.filter(
            chat__participants=self.request.user
        ).select_related(
            'sender',
            'sender__profile',
            'chat'
        )
    
    def get_serializer_class(self):
        """Use creation serializer for updates"""
        if self.request.method in ['PUT', 'PATCH']:
            return MessageCreateSerializer
        return MessageSerializer
    
    def perform_update(self, serializer):
        """Update message (only by sender)"""
        message = self.get_object()
        
        if message.sender != self.request.user:
            return Response({
                'success': False,
                'message': 'You can only edit your own messages'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Mark as edited
        serializer.save()
        message.mark_as_edited()
    
    def perform_destroy(self, instance):
        """Delete message (only by sender)"""
        if instance.sender != self.request.user:
            return Response({
                'success': False,
                'message': 'You can only delete your own messages'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Soft delete
        instance.soft_delete()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_message_read(request, message_id):
    """
    POST /api/messaging/messages/{id}/read/ - Mark message as read
    """
    try:
        # Get message from a chat user participates in
        message = get_object_or_404(
            Message.objects.filter(chat__participants=request.user),
            id=message_id
        )
        
        # Can't mark own messages as read
        if message.sender == request.user:
            return Response({
                'success': False,
                'message': 'Cannot mark your own message as read'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create message status
        status_record, created = MessageStatus.objects.get_or_create(
            message=message,
            user=request.user
        )
        
        # Mark as read
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
    """
    POST /api/messaging/messages/{id}/delivered/ - Mark message as delivered
    """
    try:
        # Get message from a chat user participates in
        message = get_object_or_404(
            Message.objects.filter(chat__participants=request.user),
            id=message_id
        )
        
        # Can't mark own messages as delivered
        if message.sender == request.user:
            return Response({
                'success': False,
                'message': 'Cannot mark your own message as delivered'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create message status
        status_record, created = MessageStatus.objects.get_or_create(
            message=message,
            user=request.user
        )
        
        # Mark as delivered
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


class SearchUsersAPIView(generics.ListAPIView):
    """
    GET /api/messaging/search/users/?q=john - Search users to start chat with
    """
    serializer_class = ChatParticipantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Search users by username or full name"""
        query = self.request.GET.get('q', '').strip()
        
        if not query or len(query) < 2:
            return User.objects.none()
        
        # Exclude current user from results
        queryset = User.objects.exclude(
            id=self.request.user.id
        ).filter(
            Q(username__icontains=query) |
            Q(full_name__icontains=query)
        ).select_related('profile')
        
        # Limit results
        return queryset[:20]


class ChatParticipantsAPIView(generics.ListAPIView):
    """
    GET /api/messaging/chats/{id}/participants/ - List chat participants
    """
    serializer_class = ChatParticipantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get participants of specific chat"""
        chat_id = self.kwargs['chat_id']
        
        # Verify user is participant in chat
        chat = get_object_or_404(
            Chat.objects.filter(participants=self.request.user),
            id=chat_id
        )
        
        return chat.participants.select_related('profile')


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_chat_participant(request, chat_id, user_id):
    """
    POST /api/messaging/chats/{id}/participants/{user_id}/ - Add participant
    DELETE /api/messaging/chats/{id}/participants/{user_id}/ - Remove participant
    """
    try:
        # Get chat user participates in
        chat = get_object_or_404(
            Chat.objects.filter(participants=request.user),
            id=chat_id
        )
        
        # Get user to add/remove
        target_user = get_object_or_404(User, id=user_id)
        
        if request.method == 'POST':
            # Add participant (only for group chats)
            if not chat.is_group_chat:
                return Response({
                    'success': False,
                    'message': 'Cannot add participants to direct messages'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if already participant
            if chat.participants.filter(id=user_id).exists():
                return Response({
                    'success': False,
                    'message': 'User is already a participant'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Add participant
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
            
            # Can't remove yourself using this endpoint
            if target_user == request.user:
                return Response({
                    'success': False,
                    'message': 'Use chat delete endpoint to leave chat'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Remove participant
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


# Function views are used directly in URLs without .as_view()