"""
API Security Module for MFA System Creator
Prevents tenants from disconnecting from the system creator control panel
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
import json
import logging

from .models import MFATenant, MFASystemConnection

logger = logging.getLogger(__name__)


def check_connection_permissions(user, tenant):
    """
    Check if user has permission to modify connection settings
    Only system administrators can modify critical connection settings
    """
    # Only superusers can modify connection security settings
    if not user.is_superuser:
        return False, "Only system administrators can modify connection settings"
    
    return True, "Permission granted"


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def disconnect_tenant(request, tenant_id):
    """
    API endpoint to disconnect tenant - RESTRICTED
    Only system administrators can disconnect tenants
    """
    try:
        tenant = get_object_or_404(MFATenant, id=tenant_id)
        connection = get_object_or_404(MFASystemConnection, tenant=tenant)
        
        # Check permissions
        has_permission, message = check_connection_permissions(request.user, tenant)
        if not has_permission:
            logger.warning(f"Unauthorized disconnect attempt by {request.user.username} for tenant {tenant.name}")
            return JsonResponse({
                'success': False,
                'error': message,
                'code': 'PERMISSION_DENIED'
            }, status=403)
        
        # Check if disconnection is allowed by security settings
        if not connection.disconnect_allowed():
            logger.warning(f"Disconnect blocked by security settings for tenant {tenant.name}")
            return JsonResponse({
                'success': False,
                'error': 'Disconnection is blocked by security settings',
                'details': {
                    'admin_locked': connection.admin_locked,
                    'force_connection': connection.force_connection,
                    'can_disconnect': connection.can_disconnect
                },
                'code': 'DISCONNECT_BLOCKED'
            }, status=403)
        
        # Perform disconnection
        connection.is_connected = False
        connection.connection_status = 'disconnected'
        connection.save()
        
        # Log the disconnection
        logger.info(f"Tenant {tenant.name} disconnected by admin {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': f'Tenant {tenant.name} has been disconnected',
            'tenant_id': tenant_id
        })
        
    except Exception as e:
        logger.error(f"Error disconnecting tenant {tenant_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def modify_connection_security(request, tenant_id):
    """
    API endpoint to modify connection security settings
    Only superusers can modify these critical settings
    """
    try:
        tenant = get_object_or_404(MFATenant, id=tenant_id)
        connection = get_object_or_404(MFASystemConnection, tenant=tenant)
        
        # Only superusers can modify security settings
        if not request.user.is_superuser:
            logger.warning(f"Unauthorized security modification attempt by {request.user.username} for tenant {tenant.name}")
            return JsonResponse({
                'success': False,
                'error': 'Only superusers can modify security settings',
                'code': 'SUPERUSER_REQUIRED'
            }, status=403)
        
        data = json.loads(request.body)
        
        # Update security settings
        if 'admin_locked' in data:
            connection.admin_locked = data['admin_locked']
        if 'force_connection' in data:
            connection.force_connection = data['force_connection']
        if 'can_disconnect' in data:
            connection.can_disconnect = data['can_disconnect']
        
        connection.save()
        
        # Log the security change
        logger.info(f"Security settings modified for tenant {tenant.name} by superuser {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Security settings updated successfully',
            'settings': {
                'admin_locked': connection.admin_locked,
                'force_connection': connection.force_connection,
                'can_disconnect': connection.can_disconnect
            }
        })
        
    except Exception as e:
        logger.error(f"Error modifying security settings for tenant {tenant_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }, status=500)


@login_required
def get_connection_status(request, tenant_id):
    """
    Get connection status and security settings for a tenant
    """
    try:
        tenant = get_object_or_404(MFATenant, id=tenant_id)
        
        try:
            connection = tenant.mfa_connection
        except MFASystemConnection.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No connection found for this tenant',
                'code': 'NO_CONNECTION'
            }, status=404)
        
        # Return connection status
        return JsonResponse({
            'success': True,
            'connection': {
                'is_connected': connection.is_connected,
                'connection_status': connection.connection_status,
                'last_sync': connection.last_sync.isoformat() if connection.last_sync else None,
                'can_tenant_modify': connection.can_tenant_modify(),
                'disconnect_allowed': connection.disconnect_allowed(),
                'security_settings': {
                    'admin_locked': connection.admin_locked,
                    'force_connection': connection.force_connection,
                    'can_disconnect': connection.can_disconnect
                } if request.user.is_superuser else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting connection status for tenant {tenant_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }, status=500)


def tenant_api_middleware(get_response):
    """
    Middleware to intercept and block tenant API calls that attempt to disconnect
    """
    def middleware(request):
        # Check if this is a tenant API call attempting to disconnect
        if request.path.startswith('/api/tenant/') and 'disconnect' in request.path:
            logger.warning(f"Blocked tenant disconnect attempt from {request.META.get('REMOTE_ADDR')}")
            return JsonResponse({
                'success': False,
                'error': 'Disconnection is not allowed through tenant API',
                'message': 'Contact system administrator to modify connection settings',
                'code': 'DISCONNECT_FORBIDDEN'
            }, status=403)
        
        response = get_response(request)
        return response
    
    return middleware
