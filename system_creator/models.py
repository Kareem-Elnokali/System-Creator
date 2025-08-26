from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json


class MFATenant(models.Model):
    """Represents a website/application using the MFA system"""
    
    PLAN_CHOICES = [
        ('free', 'Free Plan'),
        ('basic', 'Basic Plan'),
        ('premium', 'Premium Plan'),
        ('enterprise', 'Enterprise Plan'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending Setup'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Website/Application name")
    domain = models.CharField(max_length=255, unique=True, help_text="Primary domain (e.g., example.com)")
    additional_domains = models.JSONField(default=list, blank=True, help_text="Additional allowed domains")
    
    # Owner/Contact
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_tenants')
    contact_email = models.EmailField()
    contact_name = models.CharField(max_length=100)
    
    # Plan & Status
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # API Keys
    api_key = models.CharField(max_length=64, unique=True, editable=False)
    api_secret = models.CharField(max_length=128, editable=False)
    
    # Usage Limits
    max_users = models.PositiveIntegerField(default=100, help_text="Maximum users allowed")
    max_monthly_authentications = models.PositiveIntegerField(default=1000)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    # Settings
    settings = models.JSONField(default=dict, help_text="Custom tenant settings")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['status']),
            models.Index(fields=['plan']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.domain})"
    
    def save(self, *args, **kwargs):
        if not self.api_key:
            import secrets
            self.api_key = secrets.token_urlsafe(32)
        if not self.api_secret:
            import secrets
            self.api_secret = secrets.token_urlsafe(64)
        super().save(*args, **kwargs)
    
    @property
    def current_users(self):
        """Get current user count for this tenant"""
        return self.usage_stats.filter(metric='active_users').order_by('-date').first()
    
    @property
    def monthly_authentications(self):
        """Get current month's authentication count"""
        from datetime import datetime
        current_month = datetime.now().replace(day=1)
        return self.usage_stats.filter(
            metric='authentications',
            date__gte=current_month
        ).aggregate(total=models.Sum('value'))['total'] or 0


class TenantFeatures(models.Model):
    """Feature flags and permissions for each tenant"""
    
    tenant = models.OneToOneField(MFATenant, on_delete=models.CASCADE, related_name='features')
    
    # MFA Methods
    enable_totp = models.BooleanField(default=True)
    enable_email = models.BooleanField(default=True)
    enable_sms = models.BooleanField(default=False)
    enable_passkeys = models.BooleanField(default=False)
    enable_backup_codes = models.BooleanField(default=True)
    
    # Advanced Features
    enable_risk_analysis = models.BooleanField(default=False)
    enable_device_tracking = models.BooleanField(default=False)
    enable_geo_blocking = models.BooleanField(default=False)
    enable_session_management = models.BooleanField(default=False)
    enable_audit_logs = models.BooleanField(default=True)
    
    # Customization
    allow_custom_branding = models.BooleanField(default=False)
    allow_custom_domains = models.BooleanField(default=False)
    allow_webhook_notifications = models.BooleanField(default=False)
    
    # API Access
    api_rate_limit_per_minute = models.PositiveIntegerField(default=60)
    api_rate_limit_per_hour = models.PositiveIntegerField(default=1000)
    
    # Support
    priority_support = models.BooleanField(default=False)
    dedicated_support = models.BooleanField(default=False)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Features for {self.tenant.name}"


class TenantUsageStats(models.Model):
    """Track usage statistics for billing and monitoring"""
    
    METRIC_CHOICES = [
        ('active_users', 'Active Users'),
        ('authentications', 'Authentication Attempts'),
        ('api_calls', 'API Calls'),
        ('storage_used', 'Storage Used (MB)'),
        ('bandwidth_used', 'Bandwidth Used (MB)'),
    ]
    
    tenant = models.ForeignKey(MFATenant, on_delete=models.CASCADE, related_name='usage_stats')
    metric = models.CharField(max_length=50, choices=METRIC_CHOICES)
    value = models.PositiveIntegerField()
    date = models.DateField()
    
    class Meta:
        unique_together = ['tenant', 'metric', 'date']
        indexes = [
            models.Index(fields=['tenant', 'metric', 'date']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.metric}: {self.value} ({self.date})"


class TenantNotification(models.Model):
    """System notifications for tenant owners"""
    
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('billing', 'Billing'),
        ('security', 'Security Alert'),
    ]
    
    tenant = models.ForeignKey(MFATenant, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tenant.name} - {self.title}"


class TenantAPILog(models.Model):
    """Log API calls for monitoring and debugging"""
    
    tenant = models.ForeignKey(MFATenant, on_delete=models.CASCADE, related_name='api_logs')
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    status_code = models.PositiveSmallIntegerField()
    response_time_ms = models.PositiveIntegerField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['status_code']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.method} {self.endpoint} ({self.status_code})"


class SystemSettings(models.Model):
    """Global system settings for the MFA service"""
    
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    
    # Service Info
    service_name = models.CharField(max_length=100, default="MFA Service")
    service_description = models.TextField(blank=True)
    
    # Limits
    max_tenants_per_user = models.PositiveIntegerField(default=5)
    default_user_limit = models.PositiveIntegerField(default=100)
    default_auth_limit = models.PositiveIntegerField(default=1000)
    
    # Features
    allow_free_plan = models.BooleanField(default=True)
    require_email_verification = models.BooleanField(default=True)
    require_domain_verification = models.BooleanField(default=False)
    
    # Notifications
    admin_email = models.EmailField()
    send_usage_alerts = models.BooleanField(default=True)
    send_security_alerts = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'
    
    def __str__(self):
        return 'System Settings'
    
    @classmethod
    def load(cls):
        """Return the singleton settings row, creating if needed"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class MFASystemConnection(models.Model):
    """Connection settings to the main MFA system - Only system admins can modify"""
    
    tenant = models.OneToOneField(MFATenant, on_delete=models.CASCADE, related_name='mfa_connection')
    
    # Connection details - Protected from tenant modification
    mfa_system_url = models.URLField(help_text="URL of the MFA system API")
    connection_key = models.CharField(max_length=128, help_text="Key for connecting to MFA system")
    
    # Status - Only system can modify
    is_connected = models.BooleanField(default=False)
    last_sync = models.DateTimeField(null=True, blank=True)
    connection_status = models.CharField(max_length=50, default='pending')
    
    # Security controls
    can_disconnect = models.BooleanField(default=False, help_text="Only system admins can enable disconnection")
    force_connection = models.BooleanField(default=True, help_text="Force connection - tenant cannot disable")
    admin_locked = models.BooleanField(default=True, help_text="Connection locked by system administrator")
    
    # Statistics from MFA system
    total_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    total_authentications = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"MFA Connection for {self.tenant.name}"
    
    def can_tenant_modify(self):
        """Check if tenant can modify this connection"""
        return not self.admin_locked and self.can_disconnect
    
    def disconnect_allowed(self):
        """Check if disconnection is allowed"""
        return self.can_disconnect and not self.force_connection and not self.admin_locked
