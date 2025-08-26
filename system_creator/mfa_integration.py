"""
MFA System Integration Module
Handles communication with the main MFA system API
"""
import requests
import json
from django.conf import settings
from django.utils import timezone
from .models import MFASystemConnection, TenantUsageStats, TenantAPILog
import logging

logger = logging.getLogger(__name__)


class MFASystemAPI:
    """API client for communicating with the main MFA system"""
    
    def __init__(self, tenant=None):
        self.tenant = tenant
        self.base_url = getattr(settings, 'MFA_SYSTEM_API_URL', 'http://localhost:8000/mfa/api/')
        self.api_key = getattr(settings, 'MFA_SYSTEM_API_KEY', '')
        self.timeout = 30
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to MFA system API"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }
        
        if self.tenant:
            headers['X-Tenant-ID'] = str(self.tenant.id)
            headers['X-Tenant-Key'] = self.tenant.api_key
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=self.timeout
            )
            
            # Log API call
            if self.tenant:
                TenantAPILog.objects.create(
                    tenant=self.tenant,
                    endpoint=endpoint,
                    method=method.upper(),
                    status_code=response.status_code,
                    response_time_ms=int(response.elapsed.total_seconds() * 1000),
                    ip_address='127.0.0.1',  # Internal API call
                    user_agent='MFA-Control-Panel/1.0'
                )
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"MFA API request failed: {e}")
            raise MFAAPIException(f"API request failed: {e}")
    
    def get_tenant_stats(self):
        """Get statistics for the tenant from MFA system"""
        if not self.tenant:
            raise ValueError("Tenant required for stats")
        
        try:
            data = self._make_request('GET', 'tenant/stats/')
            return {
                'total_users': data.get('total_users', 0),
                'active_users': data.get('active_users', 0),
                'total_authentications': data.get('total_authentications', 0),
                'monthly_authentications': data.get('monthly_authentications', 0),
                'success_rate': data.get('success_rate', 0),
            }
        except Exception as e:
            logger.error(f"Failed to get tenant stats: {e}")
            return {}
    
    def sync_tenant_data(self):
        """Sync tenant data with MFA system"""
        if not self.tenant:
            raise ValueError("Tenant required for sync")
        
        try:
            # Get latest stats from MFA system
            stats = self.get_tenant_stats()
            
            # Update connection record
            connection, created = MFASystemConnection.objects.get_or_create(
                tenant=self.tenant,
                defaults={
                    'mfa_system_url': self.base_url,
                    'connection_key': self.tenant.api_key,
                }
            )
            
            connection.total_users = stats.get('total_users', 0)
            connection.active_users = stats.get('active_users', 0)
            connection.total_authentications = stats.get('total_authentications', 0)
            connection.is_connected = True
            connection.last_sync = timezone.now()
            connection.connection_status = 'connected'
            connection.save()
            
            # Update usage stats
            today = timezone.now().date()
            
            # Active users
            TenantUsageStats.objects.update_or_create(
                tenant=self.tenant,
                metric='active_users',
                date=today,
                defaults={'value': stats.get('active_users', 0)}
            )
            
            # Monthly authentications
            TenantUsageStats.objects.update_or_create(
                tenant=self.tenant,
                metric='authentications',
                date=today,
                defaults={'value': stats.get('monthly_authentications', 0)}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync tenant data: {e}")
            if hasattr(self, 'tenant') and self.tenant:
                connection = MFASystemConnection.objects.filter(tenant=self.tenant).first()
                if connection:
                    connection.is_connected = False
                    connection.connection_status = 'error'
                    connection.save()
            return False
    
    def register_tenant(self, tenant_data):
        """Register a new tenant with the MFA system"""
        try:
            data = self._make_request('POST', 'tenant/register/', data=tenant_data)
            return data
        except Exception as e:
            logger.error(f"Failed to register tenant: {e}")
            raise
    
    def update_tenant_features(self, features_data):
        """Update tenant features in the MFA system"""
        if not self.tenant:
            raise ValueError("Tenant required for feature update")
        
        try:
            data = self._make_request('PUT', 'tenant/features/', data=features_data)
            return data
        except Exception as e:
            logger.error(f"Failed to update tenant features: {e}")
            raise
    
    def get_tenant_users(self, limit=100, offset=0):
        """Get list of users for the tenant"""
        if not self.tenant:
            raise ValueError("Tenant required for user list")
        
        try:
            params = {'limit': limit, 'offset': offset}
            data = self._make_request('GET', 'tenant/users/', params=params)
            return data
        except Exception as e:
            logger.error(f"Failed to get tenant users: {e}")
            return {'users': [], 'total': 0}
    
    def get_authentication_logs(self, days=7, limit=100):
        """Get authentication logs for the tenant"""
        if not self.tenant:
            raise ValueError("Tenant required for auth logs")
        
        try:
            params = {'days': days, 'limit': limit}
            data = self._make_request('GET', 'tenant/auth-logs/', params=params)
            return data
        except Exception as e:
            logger.error(f"Failed to get auth logs: {e}")
            return {'logs': [], 'total': 0}


class MFAAPIException(Exception):
    """Exception raised for MFA API errors"""
    pass


def sync_all_tenants():
    """Sync data for all active tenants"""
    from .models import MFATenant
    
    active_tenants = MFATenant.objects.filter(status='active')
    results = {'success': 0, 'failed': 0, 'errors': []}
    
    for tenant in active_tenants:
        try:
            api = MFASystemAPI(tenant=tenant)
            if api.sync_tenant_data():
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"Sync failed for {tenant.name}")
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"Error syncing {tenant.name}: {e}")
    
    return results


def test_mfa_connection(tenant=None):
    """Test connection to MFA system"""
    try:
        api = MFASystemAPI(tenant=tenant)
        # Try a simple health check
        data = api._make_request('GET', 'health/')
        return {
            'success': True,
            'status': data.get('status', 'unknown'),
            'message': 'Connection successful'
        }
    except Exception as e:
        return {
            'success': False,
            'status': 'error',
            'message': str(e)
        }
