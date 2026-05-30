from .models import Maintenance, Payment, Lease
from django.db.models import Q
from datetime import date, timedelta


def notifications(request):
    if not request.user.is_authenticated:
        return {}

    open_maintenance = Maintenance.objects.filter(
        status__in=['open', 'in_progress']
    ).count()

    overdue_payments = Payment.objects.filter(status='overdue').count()

    thirty_days = date.today() + timedelta(days=30)
    expiring_leases = Lease.objects.filter(
        status='active',
        end_date__lte=thirty_days
    ).count()

    recent_maintenance = Maintenance.objects.filter(
        status__in=['open', 'in_progress']
    ).order_by('-created_at')[:3]

    return {
        'notif_open_maintenance': open_maintenance,
        'notif_overdue_payments': overdue_payments,
        'notif_expiring_leases': expiring_leases,
        'notif_total': open_maintenance + overdue_payments + expiring_leases,
        'notif_recent_maintenance': recent_maintenance,
    }
