#!/usr/bin/env python
"""
Script to create admin user with specific credentials
Run with: python create_admin.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mfa_control_panel.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_admin():
    print("Creating admin user...")
    
    # Create admin user with specified credentials
    admin_user, created = User.objects.get_or_create(
        username='5',
        defaults={
            'email': 'ad@gmail.com',
            'is_staff': True,
            'is_superuser': True,
            'first_name': 'Admin',
            'last_name': 'User'
        }
    )
    
    # Set password
    admin_user.set_password('123')
    admin_user.save()
    
    if created:
        print(f"Created new admin user: {admin_user.username}")
    else:
        print(f"Updated existing admin user: {admin_user.username}")
    
    print(f"Username: {admin_user.username}")
    print(f"Email: {admin_user.email}")
    print(f"Password: 123")
    print(f"Access the control panel at: http://localhost:8001/")
    print(f"Access Django admin at: http://localhost:8001/admin/")

if __name__ == '__main__':
    create_admin()
