"""
URL Configuration for System Creator Control Panel
"""
from django.urls import path
from . import views

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
]
