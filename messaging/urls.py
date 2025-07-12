# messaging/urls.py - FIXED VERSION FOR FUNCTION VIEWS
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # 💬 CHAT MANAGEMENT ENDPOINTS
    
    # GET /api/messaging/chats/ - List user's chats
    # POST /api/messaging/chats/ - Create new chat
    path('chats/', views.ChatListCreateAPIView.as_view(), name='chat-list-create'),
    
    # GET /api/messaging/chats/{id}/ - Get chat details with recent messages
    # PUT /api/messaging/chats/{id}/ - Update chat (name, participants)
    # DELETE /api/messaging/chats/{id}/ - Delete/leave chat
    path('chats/<uuid:pk>/', views.ChatDetailAPIView.as_view(), name='chat-detail'),
    
    # 📨 MESSAGE ENDPOINTS
    
    # GET /api/messaging/chats/{id}/messages/ - Get message history (paginated)
    # POST /api/messaging/chats/{id}/messages/ - Send new message to chat
    path('chats/<uuid:chat_id>/messages/', 
         views.ChatMessagesListCreateAPIView.as_view(), 
         name='chat-messages'),
    
    # GET /api/messaging/messages/{id}/ - Get specific message details
    # PUT /api/messaging/messages/{id}/ - Edit message (sender only)
    # DELETE /api/messaging/messages/{id}/ - Delete message (sender only)
    path('messages/<uuid:pk>/', 
         views.MessageDetailAPIView.as_view(), 
         name='message-detail'),
    
    # 📖 MESSAGE STATUS ENDPOINTS - FUNCTION VIEWS (NO .as_view())
    
    # POST /api/messaging/messages/{id}/read/ - Mark message as read
    path('messages/<uuid:message_id>/read/', 
         views.mark_message_read, 
         name='mark-message-read'),
    
    # POST /api/messaging/messages/{id}/delivered/ - Mark message as delivered
    path('messages/<uuid:message_id>/delivered/', 
         views.mark_message_delivered, 
         name='mark-message-delivered'),
    
    # 🔍 SEARCH & DISCOVERY ENDPOINTS
    
    # GET /api/messaging/search/users/?q=john - Search users to start chat with
    path('search/users/', views.SearchUsersAPIView.as_view(), name='search-users'),
    
    # 📊 UTILITY ENDPOINTS
    
    # GET /api/messaging/chats/{id}/participants/ - List chat participants
    path('chats/<uuid:chat_id>/participants/', 
         views.ChatParticipantsAPIView.as_view(), 
         name='chat-participants'),
    
    # POST /api/messaging/chats/{id}/participants/{user_id}/ - Add participant to chat
    # DELETE /api/messaging/chats/{id}/participants/{user_id}/ - Remove participant
    path('chats/<uuid:chat_id>/participants/<int:user_id>/', 
         views.manage_chat_participant, 
         name='chat-participant-manage'),
]