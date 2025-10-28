"""storeapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib.auth.decorators import login_required
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.shortcuts import render

# Define a custom view for handling "page not found" errors
@login_required()
def page_notfound(request):

    return render(request, 'page_notFound/page_not_found.html', status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('django.contrib.auth.urls')),
    path('', include('user_auth.urls')),
    path('', include('user_setup.urls')),
    path('', include('item_pos.urls')),
    path('', include('item_setup.urls')),
    path('', include('others_setup.urls')),
    path('', include('supplier_setup.urls')),
    path('', include('store_setup.urls')),
    path('', include('opening_stock.urls')),
    path('', include('invoice_list.urls')),
    path('', include('module_setup.urls')),
    path('', include('sales_report.urls')),
    path('', include('collection_report.urls')),
    path('', include('refund_due_collection.urls')),
    path('', include('G_R_N_with_without.urls')),
    path('', include('organizations.urls')),
    path('', include('stock_list.urls')),
    path('', include('consumption_report.urls')),
    path('', include('re_order_item.urls')),
    path('', include('setup_modes.urls')),
    path('', include('purchase_order.urls')),
    path('', include('po_receive.urls')),
    path('', include('po_return.urls')),
    path('', include('po_return_receive.urls')),
    path('', include('department.urls')),
    path('', include('credit_management.urls')),
    path('', include('b2b_clients_management.urls')),
    path('', include('drivers_setup.urls')),
    path('', include('post_order_update.urls')),
    path('', include('stock_reconciliation.urls')),
    path('', include('bank_setup.urls')),
    path('', include('bank_statement.urls')),
    path('', include('registrations.urls')),
    path('', include('bill_templates.urls')),
    path('', include('select_bill_receipt.urls')),
    path('', include('store_transfers.urls')),
    path('', include('deliver_chalan.urls')),
    path('', include('clients_transection.urls')),
    path('', include('local_purchase.urls')),
    path('', include('local_purchase_return.urls')),
    path('', include('manual_return_receive.urls')),
    path('', include('item_barcode.urls')),
    path('', include('login_theme.urls')),
    path('', include('reg_client_collections.urls')),
    path('', include('jarvis_assistant.urls')),
    path('', include('third_party_sender.urls')),
    path('', include('others_collection_reports.urls')),
    path('statistics/', include('statistics_dashboard.urls', namespace='statistics_dashboard')),
]

# Add a catch-all URL pattern for "page not found" errors
urlpatterns += [
    re_path(r'^.*/$', page_notfound, name='page_notfound'),
]

# Serve media files only if DEBUG is True
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)