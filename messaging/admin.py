# messaging/admin.py - COMPLETE ADMIN INTERFACE FOR MESSAGING
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Chat, Message, MessageStatus


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    """
    Admin interface for Chat model
    """
    list_display = [
        'id', 
        'chat_display_name', 
        'participants_count', 
        'is_group_chat', 
        'last_activity',
        'messages_count'
    ]
    list_filter = [
        'is_group_chat', 
        'created_at', 
        'last_activity'
    ]
    search_fields = [
        'chat_name', 
        'participants__username', 
        'participants__full_name'
    ]
    readonly_fields = [
        'id', 
        'created_at', 
        'updated_at', 
        'last_activity'
    ]
    filter_horizontal = ['participants']
    
    def chat_display_name(self, obj):
        """Display chat name or participants"""
        if obj.is_group_chat and obj.chat_name:
            return obj.chat_name
        elif obj.participants.count() <= 2:
            users = list(obj.participants.all()[:2])
            if len(users) == 2:
                return f"{users[0].username} & {users[1].username}"
            elif len(users) == 1:
                return f"{users[0].username} (solo)"
        return f"Chat {str(obj.id)[:8]}..."
    chat_display_name.short_description = "Chat Name"
    
    def participants_count(self, obj):
        """Display number of participants"""
        count = obj.participants.count()
        return format_html(
            '<span style="background-color: #e8f4fd; padding: 2px 6px; border-radius: 3px;">{} users</span>',
            count
        )
    participants_count.short_description = "Participants"
    
    def messages_count(self, obj):
        """Display number of messages in chat"""
        count = obj.messages.count()
        return format_html(
            '<span style="color: #666;">{} messages</span>',
            count
        )
    messages_count.short_description = "Messages"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin interface for Message model
    """
    list_display = [
        'id',
        'sender_info',
        'chat_info', 
        'message_preview',
        'message_type',
        'created_at',
        'is_edited',
        'is_deleted'
    ]
    list_filter = [
        'message_type',
        'is_edited',
        'is_deleted',
        'created_at',
        'chat__is_group_chat'
    ]
    search_fields = [
        'content',
        'sender__username',
        'sender__full_name',
        'chat__chat_name'
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'deleted_at'
    ]
    raw_id_fields = ['chat', 'sender', 'reply_to']
    
    def sender_info(self, obj):
        """Display sender information"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.sender.username,
            obj.sender.full_name
        )
    sender_info.short_description = "Sender"
    
    def chat_info(self, obj):
        """Display chat information"""
        chat_name = obj.chat.chat_name if obj.chat.chat_name else f"Chat {str(obj.chat.id)[:8]}..."
        chat_type = "Group" if obj.chat.is_group_chat else "Direct"
        return format_html(
            '<span>{}</span><br><small style="color: #666;">({} Chat)</small>',
            chat_name,
            chat_type
        )
    chat_info.short_description = "Chat"
    
    def message_preview(self, obj):
        """Display message content preview"""
        if obj.is_deleted:
            return format_html(
                '<span style="color: #999; font-style: italic;">[Deleted Message]</span>'
            )
        
        preview = obj.content[:100]
        if len(obj.content) > 100:
            preview += "..."
        
        style = "color: #333;"
        if obj.is_edited:
            style += " background-color: #fff3cd; padding: 2px 4px; border-radius: 2px;"
            
        return format_html(
            '<span style="{}">{}</span>{}',
            style,
            preview,
            ' <small>(edited)</small>' if obj.is_edited else ''
        )
    message_preview.short_description = "Content"
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related(
            'sender', 
            'chat'
        ).prefetch_related(
            'chat__participants'
        )


@admin.register(MessageStatus)
class MessageStatusAdmin(admin.ModelAdmin):
    """
    Admin interface for MessageStatus model
    """
    list_display = [
        'id',
        'message_info',
        'user_info',
        'status_display',
        'delivered_at',
        'read_at'
    ]
    list_filter = [
        'status',
        'created_at',
        'delivered_at',
        'read_at'
    ]
    search_fields = [
        'user__username',
        'user__full_name',
        'message__content'
    ]
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    raw_id_fields = ['message', 'user']
    
    def message_info(self, obj):
        """Display message information"""
        preview = obj.message.content[:50]
        if len(obj.message.content) > 50:
            preview += "..."
        
        return format_html(
            '<span>{}</span><br><small style="color: #666;">by {}</small>',
            preview,
            obj.message.sender.username
        )
    message_info.short_description = "Message"
    
    def user_info(self, obj):
        """Display user information"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.user.username,
            obj.user.full_name
        )
    user_info.short_description = "User"
    
    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            'sent': '#6c757d',
            'delivered': '#007bff', 
            'read': '#28a745'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display()
        )
    status_display.short_description = "Status"
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related(
            'message',
            'message__sender', 
            'user'
        )


# Admin site customization
admin.site.site_header = "Connectify Messaging Admin"
admin.site.site_title = "Connectify Admin"
admin.site.index_title = "Welcome to Connectify Administration"