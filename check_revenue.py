import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_management.settings')
django.setup()
from core.models import Payment
from django.db.models import Sum
q = Payment.objects.filter(status='paid').values('property__name').annotate(t=Sum('amount')).order_by('-t')
for x in q:
    print(x['property__name'] + ': KSh ' + format(float(x['t']), ',.0f'))
print('---')
total = Payment.objects.filter(status='paid').aggregate(s=Sum('amount'))['s'] or 0
print('Total: KSh ' + format(float(total), ',.0f'))
