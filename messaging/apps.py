# messaging/apps.py - COMPLETE APP CONFIGURATION
from django.apps import AppConfig


class MessagingConfig(AppConfig):
    """
    Configuration for the messaging app
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messaging'
    verbose_name = 'Messaging System'
    
    def ready(self):
        """
        Import signal handlers when the app is ready
        This ensures our automatic signal handlers are registered
        """
        import messaging.models  # This will register the signals