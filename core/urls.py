from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),

    # Properties
    path('properties/', views.property_list, name='property_list'),
    path('properties/add/', views.property_add, name='property_add'),
    path('properties/<int:pk>/', views.property_view, name='property_view'),
    path('properties/<int:pk>/edit/', views.property_edit, name='property_edit'),
    path('properties/<int:pk>/delete/', views.property_delete, name='property_delete'),

    # Tenants
    path('tenants/', views.tenant_list, name='tenant_list'),
    path('tenants/add/', views.tenant_add, name='tenant_add'),
    path('tenants/<int:pk>/', views.tenant_view, name='tenant_view'),
    path('tenants/<int:pk>/edit/', views.tenant_edit, name='tenant_edit'),
    path('tenants/<int:pk>/delete/', views.tenant_delete, name='tenant_delete'),

    # Leases
    path('leases/', views.lease_list, name='lease_list'),
    path('leases/add/', views.lease_add, name='lease_add'),
    path('leases/<int:pk>/edit/', views.lease_edit, name='lease_edit'),
    path('leases/<int:pk>/delete/', views.lease_delete, name='lease_delete'),

    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/', views.payment_add, name='payment_add'),
    path('payments/<int:pk>/edit/', views.payment_edit, name='payment_edit'),
    path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),

    # Maintenance
    path('maintenance/', views.maintenance_list, name='maintenance_list'),
    path('maintenance/add/', views.maintenance_add, name='maintenance_add'),
    path('maintenance/<int:pk>/edit/', views.maintenance_edit, name='maintenance_edit'),
    path('maintenance/<int:pk>/delete/', views.maintenance_delete, name='maintenance_delete'),

    # M-Pesa
    path('mpesa/', views.mpesa_list, name='mpesa_list'),
    path('mpesa/initiate/', views.mpesa_initiate, name='mpesa_initiate'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('mpesa/c2b/register/', views.mpesa_c2b_register, name='mpesa_c2b_register'),
    path('mpesa/c2b/simulate/', views.mpesa_c2b_simulate, name='mpesa_c2b_simulate'),
    path('mpesa/c2b/simulate-api/', views.mpesa_c2b_simulate_api, name='mpesa_c2b_simulate_api'),
    path('mpesa/c2b/validation/', views.mpesa_c2b_validation, name='mpesa_c2b_validation'),
    path('mpesa/c2b/confirmation/', views.mpesa_c2b_confirmation, name='mpesa_c2b_confirmation'),
    path('mpesa/<int:pk>/confirm/', views.mpesa_confirm, name='mpesa_confirm'),
    path('mpesa/<int:pk>/cancel/', views.mpesa_cancel, name='mpesa_cancel'),
    path('mpesa/<int:pk>/fail/', views.mpesa_fail, name='mpesa_fail'),

    # C2B callbacks (no "mpesa" in path — Safaricom rejects URLs with it)
    path('api/c2b/validation/', views.mpesa_c2b_validation, name='c2b_validation'),
    path('api/c2b/confirmation/', views.mpesa_c2b_confirmation, name='c2b_confirmation'),

    # Reports
    path('reports/', views.reports, name='reports'),
]
