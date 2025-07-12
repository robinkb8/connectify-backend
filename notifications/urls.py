from django.urls import path
from . import views

# Notification API URL patterns
urlpatterns = [
    # Notification list and management
    path('', views.NotificationListAPIView.as_view(), name='notification_list'),
    path('<int:pk>/', views.NotificationDetailAPIView.as_view(), name='notification_detail'),
    
    # Notification actions
    path('<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('clear-read/', views.clear_read_notifications, name='clear_read_notifications'),
    
    # Notification settings
    path('settings/', views.NotificationSettingsAPIView.as_view(), name='notification_settings'),
    
    # Notification statistics
    path('stats/', views.notification_stats, name='notification_stats'),
    path('unread-count/', views.unread_count, name='notification_unread_count'),
]