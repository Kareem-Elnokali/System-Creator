"""
URL configuration for MFA Control Panel project.
Standalone system for managing multiple websites using MFA services.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # System Creator Control Panel (main interface)
    path('', include('system_creator.urls')),
    
    # Redirect root to dashboard
    path('dashboard/', RedirectView.as_view(url='/', permanent=False)),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
