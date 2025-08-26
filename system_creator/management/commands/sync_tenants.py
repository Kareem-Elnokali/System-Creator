"""
Management command to sync tenant data with MFA systems
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from system_creator.mfa_integration import sync_all_tenants
from system_creator.models import MFATenant


class Command(BaseCommand):
    help = 'Sync tenant data with their respective MFA systems'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='Sync specific tenant by ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )

    def handle(self, *args, **options):
        if options['tenant_id']:
            # Sync specific tenant
            try:
                tenant = MFATenant.objects.get(id=options['tenant_id'])
                self.stdout.write(f"Syncing tenant: {tenant.name}")
                
                if not options['dry_run']:
                    from system_creator.mfa_integration import MFASystemAPI
                    api = MFASystemAPI(tenant=tenant)
                    success = api.sync_tenant_data()
                    
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f'Successfully synced {tenant.name}')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'Failed to sync {tenant.name}')
                        )
                else:
                    self.stdout.write("DRY RUN: Would sync this tenant")
                    
            except MFATenant.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Tenant with ID {options["tenant_id"]} not found')
                )
        else:
            # Sync all tenants
            self.stdout.write("Syncing all active tenants...")
            
            if not options['dry_run']:
                results = sync_all_tenants()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Sync completed: {results["success"]} successful, {results["failed"]} failed'
                    )
                )
                
                if results['errors']:
                    self.stdout.write(self.style.ERROR("Errors:"))
                    for error in results['errors']:
                        self.stdout.write(f"  - {error}")
            else:
                active_count = MFATenant.objects.filter(status='active').count()
                self.stdout.write(f"DRY RUN: Would sync {active_count} active tenants")
