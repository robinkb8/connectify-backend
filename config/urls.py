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

    path('api/', include('core.urls')),
]
# ✅ ADD THIS: Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)