#!/usr/bin/env python
"""
Script to create test data for MFA System Creator
Run with: python create_test_data.py
"""
import os
import sys
import django
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mfa_control_panel.settings')
django.setup()

from system_creator.models import (
    MFATenant, TenantFeatures, TenantUsageStats, 
    TenantNotification, SystemSettings
)
from django.utils import timezone
from datetime import timedelta
import uuid

User = get_user_model()

def create_test_data():
    print("Creating test data for MFA System Creator...")
    
    # Create admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@localhost',
            'is_staff': True,
            'is_superuser': True,
            'first_name': 'System',
            'last_name': 'Administrator'
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"Created admin user: {admin_user.username}")
    else:
        print(f"Admin user already exists: {admin_user.username}")
    
    # Create test tenants
    tenants_data = [
        {
            'name': 'Acme Corporation',
            'domain': 'acme.com',
            'plan': 'enterprise',
            'status': 'active',
            'max_users': 1000,
            'max_monthly_authentications': 50000,
            'contact_name': 'John Smith',
            'contact_email': 'john@acme.com'
        },
        {
            'name': 'TechStart Inc',
            'domain': 'techstart.io',
            'plan': 'premium',
            'status': 'active',
            'max_users': 500,
            'max_monthly_authentications': 25000,
            'contact_name': 'Sarah Johnson',
            'contact_email': 'sarah@techstart.io'
        },
        {
            'name': 'Local Business',
            'domain': 'localbiz.com',
            'plan': 'basic',
            'status': 'active',
            'max_users': 100,
            'max_monthly_authentications': 5000,
            'contact_name': 'Mike Wilson',
            'contact_email': 'mike@localbiz.com'
        },
        {
            'name': 'Startup Demo',
            'domain': 'startup-demo.net',
            'plan': 'free',
            'status': 'suspended',
            'max_users': 50,
            'max_monthly_authentications': 1000,
            'contact_name': 'Demo User',
            'contact_email': 'demo@startup-demo.net'
        },
        {
            'name': 'Test Company',
            'domain': 'test.localhost',
            'plan': 'basic',
            'status': 'active',
            'max_users': 200,
            'max_monthly_authentications': 10000,
            'contact_name': 'Test Admin',
            'contact_email': 'admin@test.localhost'
        }
    ]
    
    created_tenants = []
    for tenant_data in tenants_data:
        tenant, created = MFATenant.objects.get_or_create(
            domain=tenant_data['domain'],
            defaults={
                **tenant_data,
                'owner': admin_user,
                'api_key': str(uuid.uuid4()).replace('-', ''),
                'api_secret': str(uuid.uuid4()).replace('-', ''),
            }
        )
        if created:
            print(f"Created tenant: {tenant.name}")
        else:
            print(f"Tenant already exists: {tenant.name}")
        created_tenants.append(tenant)
    
    # Create tenant features
    for tenant in created_tenants:
        features, created = TenantFeatures.objects.get_or_create(
            tenant=tenant,
            defaults={
                'enable_totp': True,
                'enable_email': True,
                'enable_sms': tenant.plan in ['premium', 'enterprise'],
                'enable_passkeys': tenant.plan in ['premium', 'enterprise'],
                'enable_backup_codes': True,
                'enable_risk_analysis': tenant.plan in ['premium', 'enterprise'],
                'enable_device_tracking': tenant.plan in ['premium', 'enterprise'],
                'enable_geo_blocking': tenant.plan == 'enterprise',
                'enable_session_management': tenant.plan in ['premium', 'enterprise'],
                'enable_audit_logs': tenant.plan in ['premium', 'enterprise'],
                'allow_custom_branding': tenant.plan in ['premium', 'enterprise'],
                'allow_custom_domains': tenant.plan == 'enterprise',
                'allow_webhook_notifications': tenant.plan != 'free',
                'api_rate_limit_per_minute': 60 if tenant.plan == 'free' else 120 if tenant.plan == 'basic' else 300,
                'api_rate_limit_per_hour': 1000 if tenant.plan == 'free' else 5000 if tenant.plan == 'basic' else 15000,
                'priority_support': tenant.plan in ['premium', 'enterprise'],
                'dedicated_support': tenant.plan == 'enterprise',
            }
        )
        if created:
            print(f"Created features for: {tenant.name}")
    
    # Create usage stats
    for tenant in created_tenants:
        for days_ago in range(30):
            date = timezone.now().date() - timedelta(days=days_ago)
            
            # Active users stats
            TenantUsageStats.objects.get_or_create(
                tenant=tenant,
                metric='active_users',
                date=date,
                defaults={'value': max(1, tenant.max_users // 10 + (days_ago % 5))}
            )
            
            # Authentication stats
            TenantUsageStats.objects.get_or_create(
                tenant=tenant,
                metric='authentications',
                date=date,
                defaults={'value': max(10, tenant.max_monthly_authentications // 30 + (days_ago % 20))}
            )
    
    # Create notifications
    for tenant in created_tenants[:3]:  # Only for first 3 tenants
        TenantNotification.objects.get_or_create(
            tenant=tenant,
            defaults={
                'title': 'Welcome to MFA System',
                'message': f'Your tenant {tenant.name} has been successfully configured.',
                'type': 'info',
                'is_read': False
            }
        )
    
    # Create system settings
    settings = SystemSettings.load()
    settings.service_name = "MFA System Creator"
    settings.service_description = "Multi-Factor Authentication as a Service Platform"
    settings.admin_email = "admin@localhost"
    settings.max_tenants_per_user = 10
    settings.default_user_limit = 100
    settings.default_auth_limit = 1000
    settings.allow_free_plan = True
    settings.require_email_verification = True
    settings.require_domain_verification = False
    settings.send_usage_alerts = True
    settings.send_security_alerts = True
    settings.save()
    
    print("\nTest data creation completed!")
    print(f"Created {len(created_tenants)} tenants")
    print(f"Admin user: admin / admin123")
    print(f"Access the control panel at: http://localhost:8001/")
    print(f"Access Django admin at: http://localhost:8001/admin/")

if __name__ == '__main__':
    create_test_data()
