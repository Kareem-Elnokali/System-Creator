"""
URL Configuration for System Creator Control Panel
"""
from django.urls import path
from . import views, api_security

app_name = 'system_creator'

urlpatterns = [
    # Main Views
    path('', views.dashboard, name='dashboard'),
    path('tenants/', views.tenant_list, name='tenant_list'),
    path('tenants/<uuid:tenant_id>/', views.tenant_detail, name='tenant_detail'),
    path('tenants/<uuid:tenant_id>/features/', views.tenant_features, name='tenant_features'),
    path('analytics/', views.analytics, name='analytics'),
    path('settings/', views.system_settings, name='system_settings'),
    
    # API Endpoints
    path('api/tenant-stats/', views.api_tenant_stats, name='api_tenant_stats'),
    path('api/usage-trends/', views.api_usage_trends, name='api_usage_trends'),
    path('api/tenant-action/', views.api_tenant_action, name='api_tenant_action'),
    
    # Secure connection management endpoints (Admin only)
    path('api/admin/tenant/<uuid:tenant_id>/disconnect/', api_security.disconnect_tenant, name='admin_disconnect_tenant'),
    path('api/admin/tenant/<uuid:tenant_id>/connection-security/', api_security.modify_connection_security, name='modify_connection_security'),
    path('api/tenant/<uuid:tenant_id>/connection-status/', api_security.get_connection_status, name='get_connection_status'),
]
