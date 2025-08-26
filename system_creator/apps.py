from django.apps import AppConfig


class SystemCreatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'system_creator'
    verbose_name = 'MFA System Creator Control Panel'
    
    def ready(self):
        """Initialize the app when Django starts"""
        # Import signals if needed
        pass
