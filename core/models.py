from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Property(models.Model):
    PROPERTY_TYPES = [
        ('Apartment', 'Apartment'),
        ('House', 'House'),
        ('Studio', 'Studio'),
        ('Villa', 'Villa'),
        ('Commercial', 'Commercial'),
        ('Other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('occupied', 'Occupied'),
        ('vacant', 'Vacant'),
        ('under_maintenance', 'Under Maintenance'),
    ]

    name = models.CharField(max_length=200)
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPES, default='Apartment')
    address = models.TextField()
    bedrooms = models.IntegerField(default=1)
    bathrooms = models.IntegerField(default=1)
    size_sqft = models.IntegerField(default=0)
    rent_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    deposit = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='vacant')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Properties'


class Tenant(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50)
    id_number = models.CharField(max_length=100, blank=True)
    emergency_contact = models.CharField(max_length=50, blank=True)
    emergency_name = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    occupation = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Lease(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='leases')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='leases')
    start_date = models.DateField()
    end_date = models.DateField()
    rent_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    deposit_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    terms = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def months_elapsed(self, as_of=None):
        if as_of is None:
            from django.utils import timezone
            as_of = timezone.now().date()
        end = min(self.end_date, as_of) if self.end_date else as_of
        months = (end.year - self.start_date.year) * 12 + (end.month - self.start_date.month)
        if end.day >= self.start_date.day:
            months += 1
        return max(0, months)

    def expected_total_rent(self, as_of=None):
        return self.months_elapsed(as_of) * self.rent_amount

    def __str__(self):
        return f"{self.tenant.name} - {self.property.name}"

    class Meta:
        ordering = ['-created_at']


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('M-Pesa', 'M-Pesa'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Cash', 'Cash'),
        ('Cheque', 'Cheque'),
        ('Other', 'Other'),
    ]
    PAYMENT_TYPES = [
        ('rent', 'Rent'),
        ('deposit', 'Deposit'),
        ('late_fee', 'Late Fee'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('overdue', 'Overdue'),
        ('pending', 'Pending'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='payments')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='payments')
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    payment_date = models.DateField()
    due_date = models.DateField()
    method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default='M-Pesa')
    reference = models.CharField(max_length=200, blank=True)
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPES, default='rent')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.name} - {self.amount} on {self.payment_date}"

    class Meta:
        ordering = ['-payment_date']


class MpesaTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='mpesa_transactions')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='mpesa_transactions')
    lease = models.ForeignKey(Lease, on_delete=models.SET_NULL, null=True, blank=True, related_name='mpesa_transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    phone = models.CharField(max_length=15)
    payment_type = models.CharField(max_length=50, choices=Payment.PAYMENT_TYPES, default='rent')
    checkout_request_id = models.CharField(max_length=100, unique=True)
    mpesa_receipt_number = models.CharField(max_length=100, blank=True)
    result_code = models.IntegerField(null=True, blank=True)
    result_desc = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='mpesa_transaction')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.tenant.name} - KSh {self.amount} - {self.checkout_request_id}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'M-Pesa Transaction'
        verbose_name_plural = 'M-Pesa Transactions'


class Maintenance(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='maintenance_requests')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='maintenance_requests', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='open')
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    vendor = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
