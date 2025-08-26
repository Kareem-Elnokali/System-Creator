# MFA System Creator Control Panel

A standalone Django application for managing multiple websites using MFA services as a SaaS platform. This control panel allows system owners to monitor tenants, control features, track usage, and manage the overall MFA system health.

## Features

### Multi-Tenant Management
- **Tenant Registration**: Register new websites to use the MFA system
- **Domain Management**: Support for multiple domains per tenant
- **Plan Management**: Free, Basic, Premium, and Enterprise plans
- **Status Control**: Activate, suspend, or manage tenant status

### Feature Control System
- **MFA Methods**: Control TOTP, Email OTP, SMS, Passkeys, Backup codes per tenant
- **Advanced Features**: Rate limiting, custom branding, API access, priority support
- **Feature Flags**: Granular control over what each tenant can access

### Monitoring & Analytics
- **Real-time Dashboard**: System health, tenant statistics, usage trends
- **Usage Tracking**: Monitor authentications, active users, API calls
- **Performance Metrics**: Success rates, response times, error tracking
- **Billing Preparation**: Usage-based metrics for billing systems

### Administrative Tools
- **Django Admin**: Full administrative interface for all models
- **Bulk Actions**: Mass operations on tenants and features
- **API Integration**: RESTful API for external integrations
- **Management Commands**: CLI tools for maintenance and sync

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL (recommended) or SQLite for development
- Access to the main MFA system API

### Setup

1. **Clone and Setup Environment**
```bash
cd mfa_system_creator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment Configuration**
Create a `.env` file in the project root:
```env
# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql://user:password@localhost:5432/mfa_control_panel

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# MFA System Integration
MFA_SYSTEM_API_URL=http://localhost:8000/mfa/api/
MFA_SYSTEM_API_KEY=your-mfa-system-api-key

# Security (Production)
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
```

3. **Database Setup**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

4. **Run Development Server**
```bash
python manage.py runserver
```

## Usage

### Access Points
- **Control Panel**: http://localhost:8000/
- **Admin Interface**: http://localhost:8000/admin/
- **API Endpoints**: http://localhost:8000/api/

### Main Features

#### Dashboard
- System overview with key metrics
- Tenant status distribution
- Usage trends and health indicators
- Quick actions for common tasks

#### Tenant Management
- View all registered tenants
- Filter by plan, status, domain
- Bulk operations (activate, suspend, upgrade)
- Detailed tenant information and settings

#### Feature Control
- Enable/disable MFA methods per tenant
- Configure advanced features and limits
- Set usage quotas and restrictions
- Monitor feature usage

#### Analytics
- Usage statistics and trends
- Performance monitoring
- Error tracking and alerts
- Billing and usage reports

### Management Commands

#### Sync Tenant Data
```bash
# Sync all active tenants
python manage.py sync_tenants

# Sync specific tenant
python manage.py sync_tenants --tenant-id=<uuid>

# Dry run to see what would be synced
python manage.py sync_tenants --dry-run
```

## API Integration

The system integrates with the main MFA system through RESTful APIs:

### Required MFA System Endpoints
- `GET /api/health/` - Health check
- `GET /api/tenant/stats/` - Tenant statistics
- `POST /api/tenant/register/` - Register new tenant
- `PUT /api/tenant/features/` - Update tenant features
- `GET /api/tenant/users/` - Get tenant users
- `GET /api/tenant/auth-logs/` - Get authentication logs

### Authentication
- Uses Bearer token authentication
- Tenant-specific API keys for secure access
- Request headers include tenant identification

## Models Overview

### Core Models
- **MFATenant**: Represents websites using the MFA system
- **TenantFeatures**: Feature flags and permissions per tenant
- **TenantUsageStats**: Usage tracking and billing metrics
- **MFASystemConnection**: Connection status with main MFA system

### Supporting Models
- **TenantNotification**: System notifications for tenants
- **TenantAPILog**: API usage logging and monitoring
- **SystemSettings**: Global system configuration

## Deployment

### Production Checklist
1. Set `DJANGO_DEBUG=False`
2. Configure secure database (PostgreSQL)
3. Set up proper email backend
4. Configure static file serving (WhiteNoise included)
5. Set security environment variables
6. Use proper web server (Gunicorn included)
7. Set up SSL/HTTPS
8. Configure monitoring and logging

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "mfa_control_panel.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Environment Variables for Production
```env
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgresql://...
DJANGO_SECRET_KEY=production-secret-key
MFA_SYSTEM_API_URL=https://your-mfa-system.com/api/
```

## Security Considerations

- All API communications use HTTPS in production
- API keys are securely stored and rotated
- Rate limiting on all endpoints
- CSRF protection enabled
- Secure headers configured
- Input validation and sanitization

## Monitoring

### Health Checks
- Database connectivity
- MFA system API connectivity
- Email service status
- System resource usage

### Logging
- All API calls logged with tenant context
- Error tracking and alerting
- Performance monitoring
- Security event logging

## Support

### Troubleshooting
1. Check `.env` file configuration
2. Verify database connectivity
3. Test MFA system API connection
4. Review Django logs for errors
5. Use management commands for diagnostics

### Common Issues
- **API Connection Failed**: Check MFA_SYSTEM_API_URL and API_KEY
- **Database Errors**: Verify DATABASE_URL and run migrations
- **Email Not Sending**: Check email configuration in .env
- **Static Files Not Loading**: Run `collectstatic` command

## Development

### Adding New Features
1. Create models in `system_creator/models.py`
2. Add admin interfaces in `system_creator/admin.py`
3. Create views in `system_creator/views.py`
4. Add templates in `templates/system_creator/`
5. Update URLs in `system_creator/urls.py`

### Testing
```bash
python manage.py test
```

### Code Style
- Follow PEP 8 guidelines
- Use Django best practices
- Document all functions and classes
- Add type hints where appropriate

## License

This project is proprietary software for MFA system management.
