import random
import string
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings
from .models import Property, Tenant, Lease, Payment, Maintenance, MpesaTransaction


@login_required
def dashboard(request):
    properties = Property.objects.all()
    tenants = Tenant.objects.filter(status='active')
    leases = Lease.objects.filter(status='active')
    payments = Payment.objects.all()
    maintenance = Maintenance.objects.all()

    total_properties = properties.count()
    occupied = properties.filter(status='occupied').count()
    vacant = properties.filter(status='vacant').count()
    total_tenants = tenants.count()
    active_leases = leases.count()

    total_collected = payments.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    open_maintenance = maintenance.filter(status__in=['open', 'in_progress']).count()

    recent_payments = payments.order_by('-payment_date')[:5]
    recent_maintenance = maintenance.order_by('-created_at')[:5]

    # Monthly revenue (last 6 months)
    monthly_labels = []
    monthly_data = []
    for i in range(5, -1, -1):
        month_start = timezone.now().replace(day=1) - timedelta(days=30 * i)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        total = Payment.objects.filter(
            status='paid',
            payment_date__gte=month_start.date(),
            payment_date__lt=month_end.date(),
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        monthly_labels.append(month_start.strftime('%b %Y'))
        monthly_data.append(float(total))

    # Revenue by property (top 6)
    prop_names = []
    prop_revenue = []
    for p in Property.objects.annotate(
        rev=Sum('payments__amount', filter=Q(payments__status='paid'))
    ).order_by('-rev')[:6]:
        prop_names.append(p.name[:15])
        prop_revenue.append(float(p.rev or 0))

    ctx = {
        'total_properties': total_properties,
        'occupied': occupied,
        'vacant': vacant,
        'total_tenants': total_tenants,
        'active_leases': active_leases,
        'total_collected': total_collected,
        'open_maintenance': open_maintenance,
        'recent_payments': recent_payments,
        'recent_maintenance': recent_maintenance,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'prop_names': prop_names,
        'prop_revenue': prop_revenue,
    }
    return render(request, 'core/dashboard.html', ctx)


@login_required
def profile(request):
    return render(request, 'core/profile.html')


# ─── Properties ───────────────────────────────────────────────

@login_required
def property_list(request):
    properties = Property.objects.all()
    query = request.GET.get('q')
    status_filter = request.GET.get('status')
    if query:
        properties = properties.filter(Q(name__icontains=query) | Q(address__icontains=query))
    if status_filter:
        properties = properties.filter(status=status_filter)
    return render(request, 'core/properties/list.html', {'properties': properties})


@login_required
def property_add(request):
    if request.method == 'POST':
        name = request.POST['name']
        property_type = request.POST['property_type']
        address = request.POST['address']
        bedrooms = int(request.POST['bedrooms'])
        bathrooms = int(request.POST['bathrooms'])
        size_sqft = int(request.POST.get('size_sqft', 0))
        rent_amount = Decimal(request.POST['rent_amount'])
        deposit = Decimal(request.POST.get('deposit', 0))
        status = request.POST['status']
        description = request.POST.get('description', '')

        Property.objects.create(
            name=name, property_type=property_type, address=address,
            bedrooms=bedrooms, bathrooms=bathrooms, size_sqft=size_sqft,
            rent_amount=rent_amount, deposit=deposit, status=status,
            description=description
        )
        messages.success(request, 'Property added successfully.')
        return redirect('property_list')
    return render(request, 'core/properties/add.html')


@login_required
def property_view(request, pk):
    property = get_object_or_404(Property, pk=pk)
    leases = property.leases.all()
    maintenance_requests = property.maintenance_requests.all()
    payments = property.payments.all()
    return render(request, 'core/properties/view.html', {
        'property': property,
        'leases': leases,
        'maintenance_requests': maintenance_requests,
        'payments': payments,
    })


@login_required
def property_edit(request, pk):
    property = get_object_or_404(Property, pk=pk)
    if request.method == 'POST':
        property.name = request.POST['name']
        property.property_type = request.POST['property_type']
        property.address = request.POST['address']
        property.bedrooms = int(request.POST['bedrooms'])
        property.bathrooms = int(request.POST['bathrooms'])
        property.size_sqft = int(request.POST.get('size_sqft', 0))
        property.rent_amount = Decimal(request.POST['rent_amount'])
        property.deposit = Decimal(request.POST.get('deposit', 0))
        property.status = request.POST['status']
        property.description = request.POST.get('description', '')
        property.save()
        messages.success(request, 'Property updated successfully.')
        return redirect('property_list')
    return render(request, 'core/properties/edit.html', {'property': property})


@login_required
def property_delete(request, pk):
    property = get_object_or_404(Property, pk=pk)
    property.delete()
    messages.success(request, 'Property deleted successfully.')
    return redirect('property_list')


# ─── Tenants ─────────────────────────────────────────────────

@login_required
def tenant_list(request):
    tenants = Tenant.objects.all()
    query = request.GET.get('q')
    if query:
        tenants = tenants.filter(Q(name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query))
    return render(request, 'core/tenants/list.html', {'tenants': tenants})


@login_required
def tenant_add(request):
    if request.method == 'POST':
        tenant = Tenant.objects.create(
            name=request.POST['name'],
            email=request.POST['email'],
            phone=request.POST['phone'],
            id_number=request.POST.get('id_number', ''),
            emergency_contact=request.POST.get('emergency_contact', ''),
            emergency_name=request.POST.get('emergency_name', ''),
            address=request.POST.get('address', ''),
            occupation=request.POST.get('occupation', ''),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Tenant added successfully.')
        return redirect('tenant_view', pk=tenant.pk)
    return render(request, 'core/tenants/add.html')


@login_required
def tenant_view(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    leases = tenant.leases.all()
    payments = tenant.payments.all()
    maintenance_requests = tenant.maintenance_requests.all()
    active_leases = tenant.leases.filter(status='active')
    total_paid = tenant.payments.filter(status__in=['paid', 'partial']).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expected = sum(l.expected_total_rent() for l in active_leases)
    balance = total_expected - total_paid
    return render(request, 'core/tenants/view.html', {
        'tenant': tenant,
        'leases': leases,
        'payments': payments,
        'maintenance_requests': maintenance_requests,
        'active_lease': active_leases.first(),
        'total_paid': total_paid,
        'balance': balance,
    })


@login_required
def tenant_edit(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    if request.method == 'POST':
        tenant.name = request.POST['name']
        tenant.email = request.POST['email']
        tenant.phone = request.POST['phone']
        tenant.id_number = request.POST.get('id_number', '')
        tenant.emergency_contact = request.POST.get('emergency_contact', '')
        tenant.emergency_name = request.POST.get('emergency_name', '')
        tenant.address = request.POST.get('address', '')
        tenant.occupation = request.POST.get('occupation', '')
        tenant.notes = request.POST.get('notes', '')
        tenant.status = request.POST['status']
        tenant.save()
        messages.success(request, 'Tenant updated successfully.')
        return redirect('tenant_list')
    return render(request, 'core/tenants/edit.html', {'tenant': tenant})


@login_required
def tenant_delete(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    tenant.delete()
    messages.success(request, 'Tenant deleted successfully.')
    return redirect('tenant_list')


# ─── Leases ──────────────────────────────────────────────────

@login_required
def lease_list(request):
    leases = Lease.objects.all()
    query = request.GET.get('q')
    status_filter = request.GET.get('status')
    if query:
        leases = leases.filter(
            Q(tenant__name__icontains=query) | Q(property__name__icontains=query)
        )
    if status_filter:
        leases = leases.filter(status=status_filter)
    return render(request, 'core/leases/list.html', {'leases': leases})


@login_required
def lease_add(request):
    if request.method == 'POST':
        property = get_object_or_404(Property, pk=request.POST['property'])
        tenant = get_object_or_404(Tenant, pk=request.POST['tenant'])
        Lease.objects.create(
            property=property,
            tenant=tenant,
            start_date=request.POST['start_date'],
            end_date=request.POST['end_date'],
            rent_amount=Decimal(request.POST['rent_amount']),
            deposit_paid=Decimal(request.POST.get('deposit_paid', 0)),
            terms=request.POST.get('terms', ''),
        )
        property.status = 'occupied'
        property.save()
        messages.success(request, 'Lease created successfully.')
        return redirect('lease_list')
    properties = Property.objects.filter(status='vacant')
    tenants = Tenant.objects.filter(status='active')
    return render(request, 'core/leases/add.html', {'properties': properties, 'tenants': tenants})


@login_required
def lease_edit(request, pk):
    lease = get_object_or_404(Lease, pk=pk)
    if request.method == 'POST':
        lease.property = get_object_or_404(Property, pk=request.POST['property'])
        lease.tenant = get_object_or_404(Tenant, pk=request.POST['tenant'])
        lease.start_date = request.POST['start_date']
        lease.end_date = request.POST['end_date']
        lease.rent_amount = Decimal(request.POST['rent_amount'])
        lease.deposit_paid = Decimal(request.POST.get('deposit_paid', 0))
        lease.status = request.POST['status']
        lease.terms = request.POST.get('terms', '')
        lease.save()
        messages.success(request, 'Lease updated successfully.')
        return redirect('lease_list')
    properties = Property.objects.all()
    tenants = Tenant.objects.all()
    return render(request, 'core/leases/edit.html', {
        'lease': lease,
        'properties': properties,
        'tenants': tenants,
    })


@login_required
def lease_delete(request, pk):
    lease = get_object_or_404(Lease, pk=pk)
    property = lease.property
    lease.delete()
    if not property.leases.filter(status='active').exists():
        property.status = 'vacant'
        property.save()
    messages.success(request, 'Lease deleted successfully.')
    return redirect('lease_list')


# ─── Payments ────────────────────────────────────────────────

@login_required
def payment_list(request):
    payments = Payment.objects.all().order_by('-payment_date', '-id')
    query = request.GET.get('q')
    status_filter = request.GET.get('status')
    if query:
        payments = payments.filter(
            Q(tenant__name__icontains=query) | Q(reference__icontains=query)
        )
    if status_filter:
        payments = payments.filter(status=status_filter)
    return render(request, 'core/payments/list.html', {'payments': payments})


@login_required
def payment_add(request):
    if request.method == 'POST':
        tenant = get_object_or_404(Tenant, pk=request.POST['tenant'])
        property = get_object_or_404(Property, pk=request.POST['property'])
        lease_id = request.POST.get('lease')
        lease = get_object_or_404(Lease, pk=lease_id) if lease_id else None
        Payment.objects.create(
            tenant=tenant,
            property=property,
            lease=lease,
            amount=Decimal(request.POST['amount']),
            payment_date=request.POST['payment_date'],
            due_date=request.POST['due_date'],
            method=request.POST['method'],
            reference=request.POST.get('reference', ''),
            payment_type=request.POST.get('payment_type', 'rent'),
            status=request.POST['status'],
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Payment recorded successfully.')
        return redirect('payment_list')
    tenants = Tenant.objects.filter(status='active')
    properties = Property.objects.all()
    leases = Lease.objects.filter(status='active')
    return render(request, 'core/payments/add.html', {
        'tenants': tenants,
        'properties': properties,
        'leases': leases,
    })


@login_required
def payment_edit(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        payment.tenant = get_object_or_404(Tenant, pk=request.POST['tenant'])
        payment.property = get_object_or_404(Property, pk=request.POST['property'])
        lease_id = request.POST.get('lease')
        payment.lease = get_object_or_404(Lease, pk=lease_id) if lease_id else None
        payment.amount = Decimal(request.POST['amount'])
        payment.payment_date = request.POST['payment_date']
        payment.due_date = request.POST['due_date']
        payment.method = request.POST['method']
        payment.reference = request.POST.get('reference', '')
        payment.payment_type = request.POST.get('payment_type', 'rent')
        payment.status = request.POST['status']
        payment.notes = request.POST.get('notes', '')
        payment.save()
        messages.success(request, 'Payment updated successfully.')
        return redirect('payment_list')
    tenants = Tenant.objects.filter(status='active')
    properties = Property.objects.all()
    leases = Lease.objects.filter(status='active')
    return render(request, 'core/payments/edit.html', {
        'payment': payment,
        'tenants': tenants,
        'properties': properties,
        'leases': leases,
    })


@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    payment.delete()
    messages.success(request, 'Payment deleted successfully.')
    return redirect('payment_list')


# ─── Maintenance ─────────────────────────────────────────────

@login_required
def maintenance_list(request):
    items = Maintenance.objects.all()
    query = request.GET.get('q')
    status_filter = request.GET.get('status')
    if query:
        items = items.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if status_filter:
        items = items.filter(status=status_filter)
    return render(request, 'core/maintenance/list.html', {'maintenance_list': items})


@login_required
def maintenance_add(request):
    if request.method == 'POST':
        property = get_object_or_404(Property, pk=request.POST['property'])
        tenant_id = request.POST.get('tenant')
        tenant = get_object_or_404(Tenant, pk=tenant_id) if tenant_id else None
        Maintenance.objects.create(
            property=property,
            tenant=tenant,
            title=request.POST['title'],
            description=request.POST['description'],
            priority=request.POST['priority'],
        )
        messages.success(request, 'Maintenance request created.')
        return redirect('maintenance_list')
    properties = Property.objects.all()
    tenants = Tenant.objects.filter(status='active')
    return render(request, 'core/maintenance/add.html', {
        'properties': properties,
        'tenants': tenants,
    })


@login_required
def maintenance_edit(request, pk):
    item = get_object_or_404(Maintenance, pk=pk)
    if request.method == 'POST':
        item.property = get_object_or_404(Property, pk=request.POST['property'])
        tenant_id = request.POST.get('tenant')
        item.tenant = get_object_or_404(Tenant, pk=tenant_id) if tenant_id else None
        item.title = request.POST['title']
        item.description = request.POST['description']
        item.priority = request.POST['priority']
        item.status = request.POST['status']
        cost = request.POST.get('cost')
        item.cost = Decimal(cost) if cost else None
        item.vendor = request.POST.get('vendor', '')
        if item.status == 'resolved' and not item.resolved_at:
            item.resolved_at = timezone.now()
        item.save()
        messages.success(request, 'Maintenance request updated.')
        return redirect('maintenance_list')
    properties = Property.objects.all()
    tenants = Tenant.objects.filter(status='active')
    return render(request, 'core/maintenance/edit.html', {
        'item': item,
        'properties': properties,
        'tenants': tenants,
    })


@login_required
def maintenance_delete(request, pk):
    item = get_object_or_404(Maintenance, pk=pk)
    item.delete()
    messages.success(request, 'Maintenance request deleted.')
    return redirect('maintenance_list')


# ─── M-Pesa ──────────────────────────────────────────────────

import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .daraja import stk_push


@login_required
def mpesa_list(request):
    transactions = MpesaTransaction.objects.all()
    tenants = Tenant.objects.annotate(
        _paid=Sum('payments__amount', filter=Q(payments__status='paid')),
        total_paid_c2b=Sum('payments__amount', filter=Q(payments__method='M-Pesa', payments__status='paid')),
        lease_count=Count('leases', filter=Q(leases__status='active')),
    ).prefetch_related(
        models.Prefetch('leases', queryset=Lease.objects.filter(status='active'), to_attr='active_leases')
    )
    for t in tenants:
        t.total_paid = t._paid or 0
        t.monthly_rent = sum(l.rent_amount for l in t.active_leases)
        t.total_owed = sum(l.expected_total_rent() for l in t.active_leases)
        t.balance = t.total_owed - t.total_paid
    return render(request, 'core/mpesa/list.html', {
        'transactions': transactions,
        'tenants': tenants,
        'c2b_shortcode': settings.DARAJA_C2B_SHORTCODE,
    })


@login_required
def mpesa_initiate(request):
    if request.method == 'POST':
        tenant = get_object_or_404(Tenant, pk=request.POST['tenant'])
        property = get_object_or_404(Property, pk=request.POST['property'])
        lease_id = request.POST.get('lease')
        lease = get_object_or_404(Lease, pk=lease_id) if lease_id else None
        amount = Decimal(request.POST['amount'])
        phone = request.POST['phone']
        payment_type = request.POST.get('payment_type', 'rent')

        try:
            result = stk_push(phone, amount)
            checkout_id = result.get('CheckoutRequestID', 'N/A')
            response_code = result.get('ResponseCode', '1')
            response_desc = result.get('ResponseDescription', 'Unknown')

            txn = MpesaTransaction.objects.create(
                tenant=tenant,
                property=property,
                lease=lease,
                amount=amount,
                phone=phone,
                payment_type=payment_type,
                checkout_request_id=checkout_id,
                result_code=int(response_code) if response_code.isdigit() else 1,
                result_desc=response_desc,
            )

            if response_code == '0':
                messages.success(request, f'STK Push sent to {phone}. Waiting for customer to enter PIN...')
                return redirect('mpesa_confirm', pk=txn.pk)
            else:
                messages.warning(request, f'Safaricom response: {response_desc}')
                return redirect('mpesa_list')

        except Exception as e:
            messages.error(request, f'Daraja API error: {e}')
            return redirect('mpesa_initiate')

    tenants = Tenant.objects.filter(status='active')
    properties = Property.objects.all()
    leases = Lease.objects.filter(status='active')
    return render(request, 'core/mpesa/initiate.html', {
        'tenants': tenants,
        'properties': properties,
        'leases': leases,
    })


@login_required
def mpesa_confirm(request, pk):
    txn = get_object_or_404(MpesaTransaction, pk=pk)
    if txn.status == 'completed':
        messages.success(request, 'Transaction completed successfully.')
        return redirect('mpesa_list')
    if txn.status == 'failed':
        messages.warning(request, 'Transaction failed. Please try again.')
        return redirect('mpesa_list')
    if txn.status == 'cancelled':
        messages.warning(request, 'Transaction was cancelled.')
        return redirect('mpesa_list')
    return render(request, 'core/mpesa/confirm.html', {'txn': txn})


@login_required
def mpesa_cancel(request, pk):
    txn = get_object_or_404(MpesaTransaction, pk=pk)
    if txn.status == 'pending':
        txn.status = 'cancelled'
        txn.result_desc = 'Cancelled by user'
        txn.save()
        messages.success(request, 'Transaction cancelled.')
    return redirect('mpesa_list')


@login_required
def mpesa_fail(request, pk):
    txn = get_object_or_404(MpesaTransaction, pk=pk)
    if txn.status == 'pending':
        txn.status = 'failed'
        txn.result_code = 1
        txn.result_desc = 'Transaction failed'
        txn.save()
        messages.success(request, 'Transaction marked as failed.')
    return redirect('mpesa_list')


@csrf_exempt
def mpesa_callback(request):
    if request.method != 'POST':
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        checkout_id = stk_callback.get('CheckoutRequestID', '')
        result_code = stk_callback.get('ResultCode', 1)
        result_desc = stk_callback.get('ResultDesc', '')

        txn = MpesaTransaction.objects.filter(checkout_request_id=checkout_id).first()
        if not txn or txn.status != 'pending':
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Transaction not found or already processed'})

        if result_code == 0:
            items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            receipt = ''
            for item in items:
                if item.get('Name') == 'MpesaReceiptNumber':
                    receipt = item.get('Value', '')
                    break
            if not receipt:
                receipt = 'MPS' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

            payment = Payment.objects.create(
                tenant=txn.tenant,
                property=txn.property,
                lease=txn.lease,
                amount=txn.amount,
                payment_date=timezone.now().date(),
                due_date=timezone.now().date(),
                method='M-Pesa',
                reference=receipt,
                payment_type=txn.payment_type,
                status='paid',
                notes=f'M-Pesa callback ({txn.phone}) - {receipt}',
            )
            txn.mpesa_receipt_number = receipt
            txn.result_code = 0
            txn.result_desc = result_desc
            txn.status = 'completed'
            txn.completed_at = timezone.now()
            txn.payment = payment
        else:
            txn.result_code = result_code
            txn.result_desc = result_desc
            txn.status = 'failed'

        txn.save()
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
    except Exception as e:
        return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)})


# ─── M-Pesa C2B (Customer pays via phone menu) ──────────────

from .daraja import c2b_register_urls


@login_required
def mpesa_c2b_register(request):
    """Register C2B validation & confirmation URLs with Safaricom."""
    try:
        result = c2b_register_urls()
        response_code = result.get('ResponseCode', '1')
        response_desc = result.get('ResponseDescription', '')
        if response_code == '0':
            messages.success(request, f'C2B URLs registered successfully! {response_desc}')
        else:
            messages.warning(request, f'Registration response: {response_desc}')
    except Exception as e:
        messages.error(request, f'C2B registration failed: {e}')
    return redirect('mpesa_list')


def get_tenant_from_account(account):
    clean = account.strip()
    if clean.startswith('+'):
        clean = clean[1:]
    tenants = Tenant.objects.filter(phone__contains=clean[3:]) if clean.startswith('254') else Tenant.objects.filter(phone__contains=clean)
    return tenants.first()


def process_c2b_payment(trans_id, trans_amount, bill_ref, msisdn, first_name='', middle_name='', last_name=''):
    """Core C2B payment logic — used by both callback and simulate."""
    if not bill_ref:
        bill_ref = msisdn

    tenant = get_tenant_from_account(bill_ref)
    if not tenant:
        tenant = Tenant.objects.filter(phone__contains=msisdn[-9:]).first()
    if not tenant:
        tenant = Tenant.objects.create(
            name=f'{first_name} {middle_name} {last_name}'.strip() or f'M-Pesa User {msisdn[-4:]}',
            email=f'mpesa{msisdn}@placeholder.local',
            phone=msisdn,
        )

    active_lease = tenant.leases.filter(status='active').first()
    prop = active_lease.property if active_lease else Property.objects.first()

    if Payment.objects.filter(reference=trans_id).exists():
        return None

    return Payment.objects.create(
        tenant=tenant,
        property=prop,
        lease=active_lease,
        amount=trans_amount,
        payment_date=timezone.now().date(),
        due_date=timezone.now().date(),
        method='M-Pesa',
        reference=trans_id,
        payment_type='rent',
        status='paid',
        notes=f'C2B auto ({msisdn} - {bill_ref})',
    )


@csrf_exempt
def mpesa_c2b_validation(request):
    if request.method != 'POST':
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Method not allowed'}, status=405)
    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})


@csrf_exempt
def mpesa_c2b_confirmation(request):
    if request.method != 'POST':
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        payment = process_c2b_payment(
            trans_id=data.get('TransID', ''),
            trans_amount=Decimal(str(data.get('TransAmount', 0))),
            bill_ref=data.get('BillRefNumber', ''),
            msisdn=data.get('MSISDN', ''),
            first_name=data.get('FirstName', ''),
            middle_name=data.get('MiddleName', ''),
            last_name=data.get('LastName', ''),
        )
        if payment is None:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Duplicate or error'})
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
    except Exception as e:
        return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)})


@login_required
def mpesa_c2b_simulate(request):
    tenants = Tenant.objects.filter(status='active')
    properties = Property.objects.all()
    if request.method == 'POST':
        trans_id = request.POST.get('trans_id', 'SIM' + datetime.now().strftime('%y%m%d%H%M%S'))
        amount = Decimal(request.POST['amount'])
        phone = request.POST['phone']
        account = request.POST.get('account', phone)
        name = request.POST.get('name', '')
        parts = name.split(' ', 2) if name else [phone, '', '']
        first = parts[0] if len(parts) > 0 else phone
        mid = parts[1] if len(parts) > 1 else ''
        last = parts[2] if len(parts) > 2 else ''

        payment = process_c2b_payment(trans_id, amount, account, phone, first, mid, last)
        if payment:
            messages.success(request, f'Simulated payment received! KSh {amount} from {payment.tenant.name} (Ref: {trans_id})')
        else:
            messages.warning(request, f'Duplicate transaction: {trans_id}')
        return redirect('mpesa_list')

    return render(request, 'core/mpesa/c2b_simulate.html', {
        'tenants': tenants,
        'properties': properties,
        'now': timezone.now(),
        'api_confirmation_url': settings.DARAJA_C2B_CONFIRMATION_URL,
    })


@login_required
def mpesa_c2b_simulate_api(request):
    """Show form (GET) or call Safaricom C2B simulate + fire local callback (POST)."""
    from .daraja import c2b_simulate_transaction
    if request.method == 'POST':
        amount = Decimal(request.POST['amount'])
        phone = request.POST['phone']
        account = request.POST.get('account', phone)
        trans_id = 'API' + datetime.now().strftime('%y%m%d%H%M%S')
        api_ok = False
        try:
            result = c2b_simulate_transaction(amount, phone, account)
            api_ok = result.get('ResponseCode') == '0'
        except Exception as e:
            messages.warning(request, f'Safaricom API call failed (ngrok?). Error: {e}')

        payment = process_c2b_payment(trans_id, amount, account, phone, 'API', 'Simulated', 'User')
        if payment:
            msg = f'KSh {amount} from {payment.tenant.name} (Ref: {trans_id})'
            if api_ok:
                msg += ' — Safaricom accepted + callback processed'
            else:
                msg += ' — processed locally (API call failed, is ngrok running?)'
            messages.success(request, msg)
        else:
            messages.warning(request, 'Duplicate transaction or error processing callback.')

        return redirect('mpesa_list')

    tenants = Tenant.objects.filter(status='active')
    return render(request, 'core/mpesa/c2b_simulate.html', {
        'tenants': tenants,
        'api_confirmation_url': settings.DARAJA_C2B_CONFIRMATION_URL,
    })


# ─── Reports ─────────────────────────────────────────────────

@login_required
def reports(request):
    total_properties = Property.objects.count()
    occupied = Property.objects.filter(status='occupied').count()
    vacant = Property.objects.filter(status='vacant').count()
    total_tenants = Tenant.objects.filter(status='active').count()
    total_collected = Payment.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    total_maintenance_cost = Maintenance.objects.filter(status='resolved').aggregate(Sum('cost'))['cost__sum'] or 0

    properties = Property.objects.annotate(
        payment_count=Count('payments'),
        total_paid=Sum('payments__amount', filter=Q(payments__status='paid'))
    )

    return render(request, 'core/reports.html', {
        'total_properties': total_properties,
        'occupied': occupied,
        'vacant': vacant,
        'total_tenants': total_tenants,
        'total_collected': total_collected,
        'total_maintenance_cost': total_maintenance_cost,
        'properties': properties,
    })
