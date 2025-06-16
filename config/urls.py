from django.contrib import admin
from django.urls import path, include

# Main project URL configuration
urlpatterns = [
    # Django Admin Interface
    path('admin/', admin.site.urls),
    
    # API Endpoints - All authentication routes
    path('api/auth/', include('authentication.urls')),
]
