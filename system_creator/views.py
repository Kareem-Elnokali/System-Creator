"""
System Creator Control Panel Views
Dashboard and management views for MFA system administrators
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta, datetime
import json

from .models import (
    MFATenant, TenantFeatures, TenantUsageStats, 
    TenantNotification, TenantAPILog, SystemSettings
)


@staff_member_required
def dashboard(request):
    """Main dashboard showing system overview"""
    
    # System stats
    total_tenants = MFATenant.objects.count()
    active_tenants = MFATenant.objects.filter(status='active').count()
    suspended_tenants = MFATenant.objects.filter(status='suspended').count()
    pending_tenants = MFATenant.objects.filter(status='pending').count()
    
    # Plan distribution
    plan_stats = MFATenant.objects.values('plan').annotate(count=Count('id'))
    
    # Recent activity (last 24 hours)
    last_24h = timezone.now() - timedelta(hours=24)
    recent_api_calls = TenantAPILog.objects.filter(timestamp__gte=last_24h).count()
    recent_registrations = MFATenant.objects.filter(created_at__gte=last_24h).count()
    
    # Top tenants by usage
    top_tenants = MFATenant.objects.annotate(
        api_calls_count=Count('api_logs')
    ).order_by('-api_calls_count')[:10]
    
    # System health indicators
    error_rate = TenantAPILog.objects.filter(
        timestamp__gte=last_24h,
        status_code__gte=400
    ).count()
    
    total_calls_24h = TenantAPILog.objects.filter(timestamp__gte=last_24h).count()
    error_percentage = (error_rate / total_calls_24h * 100) if total_calls_24h > 0 else 0
    
    context = {
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'suspended_tenants': suspended_tenants,
        'pending_tenants': pending_tenants,
        'plan_stats': plan_stats,
        'recent_api_calls': recent_api_calls,
        'recent_registrations': recent_registrations,
        'top_tenants': top_tenants,
        'error_percentage': round(error_percentage, 2),
        'system_health': 'good' if error_percentage < 5 else 'warning' if error_percentage < 15 else 'critical'
    }
    
    return render(request, 'system_creator/dashboard.html', context)


@staff_member_required
def tenant_list(request):
    """List all tenants with filtering and search"""
    
    tenants = MFATenant.objects.select_related('owner').prefetch_related('features')
    
    # Filters
    status_filter = request.GET.get('status')
    plan_filter = request.GET.get('plan')
    search = request.GET.get('search')
    
    if status_filter:
        tenants = tenants.filter(status=status_filter)
    if plan_filter:
        tenants = tenants.filter(plan=plan_filter)
    if search:
        tenants = tenants.filter(
            Q(name__icontains=search) |
            Q(domain__icontains=search) |
            Q(owner__username__icontains=search)
        )
    
    # Add usage stats
    for tenant in tenants:
        tenant.current_month_auths = tenant.monthly_authentications
        tenant.current_users_count = tenant.current_users.value if tenant.current_users else 0
    
    context = {
        'tenants': tenants,
        'status_choices': MFATenant.STATUS_CHOICES,
        'plan_choices': MFATenant.PLAN_CHOICES,
        'current_filters': {
            'status': status_filter,
            'plan': plan_filter,
            'search': search
        }
    }
    
    return render(request, 'system_creator/tenant_list.html', context)


@staff_member_required
def tenant_detail(request, tenant_id):
    """Detailed view of a specific tenant"""
    
    tenant = get_object_or_404(MFATenant, id=tenant_id)
    
    # Usage statistics for the last 30 days
    last_30_days = timezone.now() - timedelta(days=30)
    usage_stats = TenantUsageStats.objects.filter(
        tenant=tenant,
        date__gte=last_30_days.date()
    ).order_by('date')
    
    # API logs for the last 7 days
    last_7_days = timezone.now() - timedelta(days=7)
    api_logs = TenantAPILog.objects.filter(
        tenant=tenant,
        timestamp__gte=last_7_days
    ).order_by('-timestamp')[:100]
    
    # Recent notifications
    notifications = TenantNotification.objects.filter(
        tenant=tenant
    ).order_by('-created_at')[:20]
    
    # Performance metrics
    avg_response_time = api_logs.aggregate(
        avg_time=Sum('response_time_ms')
    )['avg_time'] or 0
    
    error_count = api_logs.filter(status_code__gte=400).count()
    success_rate = ((api_logs.count() - error_count) / api_logs.count() * 100) if api_logs.count() > 0 else 100
    
    context = {
        'tenant': tenant,
        'usage_stats': usage_stats,
        'api_logs': api_logs,
        'notifications': notifications,
        'avg_response_time': avg_response_time,
        'success_rate': round(success_rate, 2),
        'error_count': error_count
    }
    
    return render(request, 'system_creator/tenant_detail.html', context)


@staff_member_required
def tenant_features(request, tenant_id):
    """Manage tenant features and permissions"""
    
    tenant = get_object_or_404(MFATenant, id=tenant_id)
    features, created = TenantFeatures.objects.get_or_create(tenant=tenant)
    
    if request.method == 'POST':
        # Update features based on form data
        boolean_fields = [
            'enable_totp', 'enable_email', 'enable_sms', 'enable_passkeys', 
            'enable_backup_codes', 'enable_risk_analysis', 'enable_device_tracking',
            'enable_geo_blocking', 'enable_session_management', 'enable_audit_logs',
            'allow_custom_branding', 'allow_custom_domains', 'allow_webhook_notifications',
            'priority_support', 'dedicated_support'
        ]
        
        for field in boolean_fields:
            setattr(features, field, field in request.POST)
        
        # Update numeric fields
        features.api_rate_limit_per_minute = int(request.POST.get('api_rate_limit_per_minute', 60))
        features.api_rate_limit_per_hour = int(request.POST.get('api_rate_limit_per_hour', 1000))
        
        features.save()
        messages.success(request, f'Features updated for {tenant.name}')
        
        return redirect('tenant_detail', tenant_id=tenant.id)
    
    context = {
        'tenant': tenant,
        'features': features
    }
    
    return render(request, 'system_creator/tenant_features.html', context)


@staff_member_required
def analytics(request):
    """System analytics and reporting"""
    
    # Date range filter
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Usage trends
    daily_stats = TenantUsageStats.objects.filter(
        date__gte=start_date.date()
    ).values('date', 'metric').annotate(
        total_value=Sum('value')
    ).order_by('date')
    
    # API performance
    api_performance = TenantAPILog.objects.filter(
        timestamp__gte=start_date
    ).extra(
        select={'date': 'DATE(timestamp)'}
    ).values('date').annotate(
        total_calls=Count('id'),
        avg_response_time=Sum('response_time_ms'),
        error_count=Count('id', filter=Q(status_code__gte=400))
    ).order_by('date')
    
    # Top endpoints
    top_endpoints = TenantAPILog.objects.filter(
        timestamp__gte=start_date
    ).values('endpoint').annotate(
        call_count=Count('id'),
        avg_response_time=Sum('response_time_ms')
    ).order_by('-call_count')[:10]
    
    # Plan distribution over time
    plan_growth = MFATenant.objects.filter(
        created_at__gte=start_date
    ).extra(
        select={'date': 'DATE(created_at)'}
    ).values('date', 'plan').annotate(
        count=Count('id')
    ).order_by('date')
    
    context = {
        'days': days,
        'daily_stats': daily_stats,
        'api_performance': api_performance,
        'top_endpoints': top_endpoints,
        'plan_growth': plan_growth
    }
    
    return render(request, 'system_creator/analytics.html', context)


@staff_member_required
def system_settings(request):
    """Manage global system settings"""
    
    settings = SystemSettings.load()
    
    if request.method == 'POST':
        # Update settings
        settings.service_name = request.POST.get('service_name', settings.service_name)
        settings.service_description = request.POST.get('service_description', settings.service_description)
        settings.max_tenants_per_user = int(request.POST.get('max_tenants_per_user', settings.max_tenants_per_user))
        settings.default_user_limit = int(request.POST.get('default_user_limit', settings.default_user_limit))
        settings.default_auth_limit = int(request.POST.get('default_auth_limit', settings.default_auth_limit))
        settings.admin_email = request.POST.get('admin_email', settings.admin_email)
        
        # Boolean fields
        settings.allow_free_plan = 'allow_free_plan' in request.POST
        settings.require_email_verification = 'require_email_verification' in request.POST
        settings.require_domain_verification = 'require_domain_verification' in request.POST
        settings.send_usage_alerts = 'send_usage_alerts' in request.POST
        settings.send_security_alerts = 'send_security_alerts' in request.POST
        
        settings.save()
        messages.success(request, 'System settings updated successfully')
        
        return redirect('system_settings')
    
    context = {
        'settings': settings
    }
    
    return render(request, 'system_creator/system_settings.html', context)


# API Endpoints for AJAX calls

@staff_member_required
def api_tenant_stats(request):
    """API endpoint for tenant statistics"""
    
    stats = {
        'total': MFATenant.objects.count(),
        'active': MFATenant.objects.filter(status='active').count(),
        'suspended': MFATenant.objects.filter(status='suspended').count(),
        'pending': MFATenant.objects.filter(status='pending').count(),
    }
    
    # Plan distribution
    plan_stats = {}
    for plan, count in MFATenant.objects.values_list('plan').annotate(Count('plan')):
        plan_stats[plan] = count
    
    return JsonResponse({
        'status_stats': stats,
        'plan_stats': plan_stats
    })


@staff_member_required
def api_usage_trends(request):
    """API endpoint for usage trend data"""
    
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Daily authentication counts
    daily_auths = TenantUsageStats.objects.filter(
        metric='authentications',
        date__gte=start_date.date()
    ).values('date').annotate(
        total=Sum('value')
    ).order_by('date')
    
    # Daily API calls
    daily_api_calls = TenantAPILog.objects.filter(
        timestamp__gte=start_date
    ).extra(
        select={'date': 'DATE(timestamp)'}
    ).values('date').annotate(
        total=Count('id')
    ).order_by('date')
    
    return JsonResponse({
        'daily_auths': list(daily_auths),
        'daily_api_calls': list(daily_api_calls)
    })


@staff_member_required
def api_tenant_action(request):
    """API endpoint for tenant actions (activate, suspend, etc.)"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = json.loads(request.body)
        tenant_id = data.get('tenant_id')
        action = data.get('action')
        
        tenant = get_object_or_404(MFATenant, id=tenant_id)
        
        if action == 'activate':
            tenant.status = 'active'
            tenant.save()
            message = f'Tenant {tenant.name} activated'
            
        elif action == 'suspend':
            tenant.status = 'suspended'
            tenant.save()
            message = f'Tenant {tenant.name} suspended'
            
        elif action == 'regenerate_keys':
            import secrets
            tenant.api_key = secrets.token_urlsafe(32)
            tenant.api_secret = secrets.token_urlsafe(64)
            tenant.save()
            message = f'API keys regenerated for {tenant.name}'
            
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)
        
        return JsonResponse({
            'success': True,
            'message': message,
            'tenant': {
                'id': str(tenant.id),
                'status': tenant.status,
                'api_key': tenant.api_key if action == 'regenerate_keys' else None
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
