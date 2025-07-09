# config/urls.py - UPDATED WITH MESSAGING AND PAYMENTS ROUTES
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


# Main project URL configuration
urlpatterns = [
    # Django Admin Interface
    path('admin/', admin.site.urls),
    
    # API Endpoints - All authentication routes
    path('api/auth/', include('authentication.urls')),

    # Core app routes (posts, likes, comments)
    path('api/', include('core.urls')),
    
    # Messaging system routes
    path('api/messaging/', include('messaging.urls')),

    # Notifications system routes
    path('api/notifications/', include('notifications.urls')),
    
    # Payments system routes
    path('api/payments/', include('payments.urls')),
]

# ✅ Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)