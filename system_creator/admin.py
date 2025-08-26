"""
System Creator Admin Interface
Comprehensive admin for managing MFA tenants and system settings
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import (
    MFATenant, TenantFeatures, TenantUsageStats, 
    TenantNotification, TenantAPILog, SystemSettings
)


@admin.register(MFATenant)
class MFATenantAdmin(admin.ModelAdmin):
    """Comprehensive tenant management with monitoring and controls"""
    
    list_display = (
        'name', 'domain', 'owner', 'plan', 'status', 
        'current_users_display', 'monthly_auths_display', 
        'health_status', 'created_at'
    )
    list_filter = ('plan', 'status', 'created_at')
    search_fields = ('name', 'domain', 'owner__username', 'contact_email')
    readonly_fields = ('id', 'api_key', 'api_secret', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'domain', 'additional_domains', 'owner', 'contact_name', 'contact_email')
        }),
        ('Plan & Status', {
            'fields': ('plan', 'status', 'max_users', 'max_monthly_authentications')
        }),
        ('API Credentials', {
            'fields': ('api_key', 'api_secret'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_activity'),
            'classes': ('collapse',)
        })
    )
    
    actions = [
        'activate_tenants', 'suspend_tenants', 'upgrade_to_basic', 
        'send_notification', 'regenerate_api_keys'
    ]
    
    def current_users_display(self, obj):
        """Display current user count with limit"""
        current = obj.current_users
        if current:
            value = current.value
            percentage = (value / obj.max_users) * 100
            color = 'red' if percentage > 90 else 'orange' if percentage > 75 else 'green'
            return format_html(
                '<span style="color: {};">{} / {}</span>',
                color, value, obj.max_users
            )
        return '0 / {}'.format(obj.max_users)
    current_users_display.short_description = 'Users'
    
    def monthly_auths_display(self, obj):
        """Display monthly authentications with limit"""
        current = obj.monthly_authentications
        percentage = (current / obj.max_monthly_authentications) * 100
        color = 'red' if percentage > 90 else 'orange' if percentage > 75 else 'green'
        return format_html(
            '<span style="color: {};">{} / {}</span>',
            color, current, obj.max_monthly_authentications
        )
    monthly_auths_display.short_description = 'Monthly Auths'
    
    def health_status(self, obj):
        """Overall health indicator"""
        if obj.status != 'active':
            return format_html('<span style="color: red;">●</span> Inactive')
        
        # Check recent API activity
        recent_activity = obj.api_logs.filter(
            timestamp__gte=timezone.now() - timedelta(days=1)
        ).exists()
        
        if recent_activity:
            return format_html('<span style="color: green;">●</span> Healthy')
        else:
            return format_html('<span style="color: orange;">●</span> Idle')
    health_status.short_description = 'Health'
    
    def activate_tenants(self, request, queryset):
        """Bulk activate selected tenants"""
        updated = queryset.update(status='active')
        self.message_user(request, f'Activated {updated} tenants.')
    activate_tenants.short_description = 'Activate selected tenants'
    
    def suspend_tenants(self, request, queryset):
        """Bulk suspend selected tenants"""
        updated = queryset.update(status='suspended')
        self.message_user(request, f'Suspended {updated} tenants.')
    suspend_tenants.short_description = 'Suspend selected tenants'
    
    def upgrade_to_basic(self, request, queryset):
        """Upgrade selected tenants to basic plan"""
        updated = queryset.update(plan='basic')
        self.message_user(request, f'Upgraded {updated} tenants to Basic plan.')
    upgrade_to_basic.short_description = 'Upgrade to Basic plan'
    
    def send_notification(self, request, queryset):
        """Send notification to selected tenants"""
        # This would open a form to compose notification
        count = queryset.count()
        self.message_user(request, f'Notification form would open for {count} tenants.')
    send_notification.short_description = 'Send notification'
    
    def regenerate_api_keys(self, request, queryset):
        """Regenerate API keys for selected tenants"""
        import secrets
        count = 0
        for tenant in queryset:
            tenant.api_key = secrets.token_urlsafe(32)
            tenant.api_secret = secrets.token_urlsafe(64)
            tenant.save()
            count += 1
        self.message_user(request, f'Regenerated API keys for {count} tenants.')
    regenerate_api_keys.short_description = 'Regenerate API keys'


@admin.register(TenantFeatures)
class TenantFeaturesAdmin(admin.ModelAdmin):
    """Manage feature flags for tenants"""
    
    list_display = (
        'tenant', 'mfa_methods_summary', 'advanced_features_summary', 
        'api_limits_summary', 'support_level'
    )
    list_filter = (
        'enable_totp', 'enable_sms', 'enable_passkeys', 
        'enable_risk_analysis', 'priority_support'
    )
    search_fields = ('tenant__name', 'tenant__domain')
    
    fieldsets = (
        ('MFA Methods', {
            'fields': (
                'enable_totp', 'enable_email', 'enable_sms', 
                'enable_passkeys', 'enable_backup_codes'
            )
        }),
        ('Advanced Security', {
            'fields': (
                'enable_risk_analysis', 'enable_device_tracking', 
                'enable_geo_blocking', 'enable_session_management', 'enable_audit_logs'
            )
        }),
        ('Customization', {
            'fields': (
                'allow_custom_branding', 'allow_custom_domains', 
                'allow_webhook_notifications'
            )
        }),
        ('API Limits', {
            'fields': ('api_rate_limit_per_minute', 'api_rate_limit_per_hour')
        }),
        ('Support', {
            'fields': ('priority_support', 'dedicated_support')
        })
    )
    
    def mfa_methods_summary(self, obj):
        """Show enabled MFA methods"""
        methods = []
        if obj.enable_totp: methods.append('TOTP')
        if obj.enable_email: methods.append('Email')
        if obj.enable_sms: methods.append('SMS')
        if obj.enable_passkeys: methods.append('Passkeys')
        if obj.enable_backup_codes: methods.append('Backup')
        return ', '.join(methods) if methods else 'None'
    mfa_methods_summary.short_description = 'MFA Methods'
    
    def advanced_features_summary(self, obj):
        """Show enabled advanced features"""
        features = []
        if obj.enable_risk_analysis: features.append('Risk Analysis')
        if obj.enable_device_tracking: features.append('Device Tracking')
        if obj.enable_geo_blocking: features.append('Geo Blocking')
        return ', '.join(features) if features else 'Basic'
    advanced_features_summary.short_description = 'Advanced Features'
    
    def api_limits_summary(self, obj):
        """Show API rate limits"""
        return f"{obj.api_rate_limit_per_minute}/min, {obj.api_rate_limit_per_hour}/hour"
    api_limits_summary.short_description = 'API Limits'
    
    def support_level(self, obj):
        """Show support level"""
        if obj.dedicated_support:
            return format_html('<span style="color: gold;">★★★ Dedicated</span>')
        elif obj.priority_support:
            return format_html('<span style="color: orange;">★★ Priority</span>')
        else:
            return format_html('<span style="color: gray;">★ Standard</span>')
    support_level.short_description = 'Support Level'


@admin.register(TenantUsageStats)
class TenantUsageStatsAdmin(admin.ModelAdmin):
    """Monitor tenant usage statistics"""
    
    list_display = ('tenant', 'metric', 'value', 'date', 'trend_indicator')
    list_filter = ('metric', 'date')
    search_fields = ('tenant__name', 'tenant__domain')
    date_hierarchy = 'date'
    
    def trend_indicator(self, obj):
        """Show trend compared to previous period"""
        previous = TenantUsageStats.objects.filter(
            tenant=obj.tenant,
            metric=obj.metric,
            date__lt=obj.date
        ).order_by('-date').first()
        
        if previous:
            change = obj.value - previous.value
            if change > 0:
                return format_html('<span style="color: green;">↗ +{}</span>', change)
            elif change < 0:
                return format_html('<span style="color: red;">↘ {}</span>', change)
            else:
                return format_html('<span style="color: gray;">→ 0</span>')
        return '—'
    trend_indicator.short_description = 'Trend'


@admin.register(TenantNotification)
class TenantNotificationAdmin(admin.ModelAdmin):
    """Manage tenant notifications"""
    
    list_display = ('tenant', 'type', 'title', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('tenant__name', 'title', 'message')
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'Marked {updated} notifications as read.')
    mark_as_read.short_description = 'Mark as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'Marked {updated} notifications as unread.')
    mark_as_unread.short_description = 'Mark as unread'


@admin.register(TenantAPILog)
class TenantAPILogAdmin(admin.ModelAdmin):
    """Monitor API usage and performance"""
    
    list_display = (
        'tenant', 'method', 'endpoint', 'status_code', 
        'response_time_display', 'ip_address', 'timestamp'
    )
    list_filter = ('method', 'status_code', 'timestamp')
    search_fields = ('tenant__name', 'endpoint', 'ip_address')
    date_hierarchy = 'timestamp'
    
    def response_time_display(self, obj):
        """Color-coded response time"""
        ms = obj.response_time_ms
        if ms < 100:
            color = 'green'
        elif ms < 500:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color: {};">{} ms</span>', color, ms)
    response_time_display.short_description = 'Response Time'
    
    def get_queryset(self, request):
        """Limit to recent logs for performance"""
        return super().get_queryset(request).filter(
            timestamp__gte=timezone.now() - timedelta(days=30)
        )


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """Global system configuration"""
    
    fieldsets = (
        ('Service Information', {
            'fields': ('service_name', 'service_description')
        }),
        ('Default Limits', {
            'fields': (
                'max_tenants_per_user', 'default_user_limit', 
                'default_auth_limit'
            )
        }),
        ('Features', {
            'fields': (
                'allow_free_plan', 'require_email_verification', 
                'require_domain_verification'
            )
        }),
        ('Notifications', {
            'fields': (
                'admin_email', 'send_usage_alerts', 'send_security_alerts'
            )
        }),
        ('Meta', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('updated_at',)
    
    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
