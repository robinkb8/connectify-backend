from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class UserAdmin(BaseUserAdmin):
    """
    Professional but simple admin interface
    """
    # Show key info in user list
    list_display = ('email', 'username', 'full_name', 'is_active', 'date_joined')
    
    # Make email and username clickable
    list_display_links = ('email', 'username')
    
    # Add search across important fields
    search_fields = ('email', 'username', 'full_name')
    
    # Add useful filters
    list_filter = ('is_active', 'date_joined')
    
    # Show newest users first
    ordering = ('-date_joined',)  # Note the minus sign for descending order
    
    # Simple form organization
    fieldsets = (
        ('User Info', {
            'fields': ('email', 'username', 'full_name', 'phone')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
    )

# Register with custom admin
admin.site.register(User, UserAdmin)

# Simple branding
admin.site.site_header = "Connectify Admin"