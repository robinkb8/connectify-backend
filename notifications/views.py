from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import Notification, NotificationSettings
from .serializers import (
    NotificationSerializer,
    NotificationUpdateSerializer,
    NotificationSettingsSerializer,
    NotificationStatsSerializer
)
from .utils import mark_notifications_read, get_unread_count


class NotificationListAPIView(generics.ListAPIView):
    """GET /api/notifications/ - Get user notifications with pagination"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get notifications for current user"""
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related(
            'sender',
            'sender__profile',
            'content_type'
        ).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """Override list to include pagination and stats"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Apply filters
        notification_type = request.query_params.get('type')
        is_read = request.query_params.get('is_read')
        
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        if is_read is not None:
            is_read_bool = is_read.lower() in ['true', '1']
            queryset = queryset.filter(is_read=is_read_bool)
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class NotificationDetailAPIView(generics.RetrieveUpdateAPIView):
    """GET/PUT /api/notifications/1/ - Get or update specific notification"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get notifications for current user"""
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related(
            'sender',
            'sender__profile',
            'content_type'
        )
    
    def get_serializer_class(self):
        """Use different serializer for updates"""
        if self.request.method in ['PUT', 'PATCH']:
            return NotificationUpdateSerializer
        return NotificationSerializer


class NotificationSettingsAPIView(generics.RetrieveUpdateAPIView):
    """GET/PUT /api/notifications/settings/ - Manage notification preferences"""
    serializer_class = NotificationSettingsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Get or create notification settings for current user"""
        settings_obj, created = NotificationSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings_obj


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """POST /api/notifications/1/read/ - Mark single notification as read"""
    try:
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user
        )
        
        if not notification.is_read:
            notification.mark_as_read()
            
            return Response({
                'success': True,
                'message': 'Notification marked as read',
                'notification_id': notification_id
            })
        else:
            return Response({
                'success': False,
                'message': 'Notification already read'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Notification.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """POST /api/notifications/mark-all-read/ - Mark all notifications as read"""
    try:
        updated_count = mark_notifications_read(request.user)
        
        return Response({
            'success': True,
            'message': f'Marked {updated_count} notifications as read',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Failed to mark notifications as read'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_stats(request):
    """GET /api/notifications/stats/ - Get notification statistics"""
    try:
        user = request.user
        
        # Get notification counts
        total_count = Notification.objects.filter(recipient=user).count()
        unread_count = get_unread_count(user)
        
        # Recent notifications (last 24 hours)
        recent_cutoff = timezone.now() - timedelta(hours=24)
        recent_count = Notification.objects.filter(
            recipient=user,
            created_at__gte=recent_cutoff
        ).count()
        
        # Breakdown by notification type
        types_breakdown = Notification.objects.filter(
            recipient=user
        ).values('notification_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Convert to dictionary
        types_dict = {item['notification_type']: item['count'] for item in types_breakdown}
        
        stats_data = {
            'total_count': total_count,
            'unread_count': unread_count,
            'recent_count': recent_count,
            'types_breakdown': types_dict
        }
        
        serializer = NotificationStatsSerializer(stats_data)
        return Response({
            'success': True,
            'stats': serializer.data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Failed to get notification stats'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, notification_id):
    """DELETE /api/notifications/1/ - Delete specific notification"""
    try:
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user
        )
        
        notification.delete()
        
        return Response({
            'success': True,
            'message': 'Notification deleted successfully'
        })
        
    except Notification.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_read_notifications(request):
    """DELETE /api/notifications/clear-read/ - Delete all read notifications"""
    try:
        deleted_count, _ = Notification.objects.filter(
            recipient=request.user,
            is_read=True
        ).delete()
        
        return Response({
            'success': True,
            'message': f'Deleted {deleted_count} read notifications',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Failed to clear read notifications'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_count(request):
    """GET /api/notifications/unread-count/ - Get unread notification count"""
    try:
        count = get_unread_count(request.user)
        
        return Response({
            'success': True,
            'unread_count': count
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Failed to get unread count'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)