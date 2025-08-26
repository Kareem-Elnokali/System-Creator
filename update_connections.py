#!/usr/bin/env python
"""
Script to update existing MFA connections with security controls
This ensures all existing tenants are locked and cannot disconnect
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mfa_control_panel.settings')
django.setup()

from system_creator.models import MFATenant, MFASystemConnection

def update_connection_security():
    print("Updating MFA connection security settings...")
    
    # Get all tenants
    tenants = MFATenant.objects.all()
    
    for tenant in tenants:
        # Create or update MFA connection with secure defaults
        connection, created = MFASystemConnection.objects.get_or_create(
            tenant=tenant,
            defaults={
                'mfa_system_url': 'http://localhost:8000/api/',  # Default MFA system URL
                'connection_key': f'key_{tenant.api_key}',
                'is_connected': True,
                'connection_status': 'active',
                'admin_locked': True,  # Locked by admin
                'force_connection': True,  # Cannot be disconnected
                'can_disconnect': False,  # Disconnection not allowed
            }
        )
        
        if created:
            print(f"Created secure connection for: {tenant.name}")
        else:
            # Update existing connection with security controls
            connection.admin_locked = True
            connection.force_connection = True
            connection.can_disconnect = False
            connection.save()
            print(f"Updated security settings for: {tenant.name}")
    
    print(f"\nSecurity update completed!")
    print(f"All {tenants.count()} tenants are now secured:")
    print("- admin_locked = True (prevents tenant modifications)")
    print("- force_connection = True (prevents disconnection)")
    print("- can_disconnect = False (blocks disconnect requests)")
    print("\nOnly system administrators can modify these settings.")

if __name__ == '__main__':
    update_connection_security()
