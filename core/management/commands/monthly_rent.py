from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from django.conf import settings
from decimal import Decimal
from core.models import Lease, Payment, Tenant


class Command(BaseCommand):
    help = 'Create rent due records for the new month and notify tenants'

    def handle(self, *args, **options):
        today = timezone.now().date()
        month_start = today.replace(day=1)
        month_end = (month_start.replace(day=28) + __import__('datetime').timedelta(days=4)).replace(day=1) - __import__('datetime').timedelta(days=1)
        month_name = today.strftime('%B %Y')

        active_leases = Lease.objects.filter(status='active')
        created = 0
        notified = 0

        for lease in active_leases:
            already_due = Payment.objects.filter(
                lease=lease, payment_type='rent',
                due_date__year=today.year, due_date__month=today.month,
            ).exists()
            if already_due:
                continue

            Payment.objects.create(
                tenant=lease.tenant, property=lease.property, lease=lease,
                amount=lease.rent_amount, payment_date=today, due_date=month_end,
                method='M-Pesa', payment_type='rent', status='pending',
                notes=f'Rent for {month_name}',
            )
            created += 1
            if self._notify_tenant(lease.tenant, lease, month_name):
                notified += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created} rent due records, notified {notified} tenants'))

    def _notify_tenant(self, tenant, lease, month_name):
        try:
            total_paid = tenant.payments.filter(status='paid').aggregate(s=Sum('amount'))['s'] or 0
            balance = lease.expected_total_rent() - total_paid

            msg = (
                f'RENT REMINDER - {month_name}\n'
                f'Hi {tenant.name}, rent of KSh {lease.rent_amount:,.0f} for '
                f'{lease.property.name} is now due. Balance: KSh {balance:,.0f}. '
                f'Pay via M-Pesa Paybill 600000, Account: {tenant.phone}'
            )

            self._send_sms(tenant.phone, msg)
            self.stdout.write(f'SMS sent to {tenant.name} ({tenant.phone})')
            return True
        except Exception as e:
            self.stderr.write(f'Failed to notify {tenant.name}: {e}')
            return False

    def _send_sms(self, phone, message):
        if not settings.AT_API_KEY:
            self.stdout.write(f'[SMS] Would send to {phone}: {message}')
            return
        import africastalking
        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        sms = africastalking.SMS
        sms.send(message, [phone])
