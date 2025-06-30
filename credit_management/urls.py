from django.urls import path
from . import views

urlpatterns = [
    path('supplier_opening_balance/', views.supplierOpeningBalanceAPI, name='supplier_opening_balance'),
    path('credit_report_services/', views.reportCreditManagerAPI, name='credit_report_modal'),
    path('list_of_clients/', views.getClientsListAPI, name='list_of_clients'),
    path('get_supplier_opening_balance_amt/', views.getSupplierOpBalAmtAPI, name='get_supplier_opening_balance_amt'),
    path('add_credit_transaction/', views.addCreditTransactionAPI, name='add_credit_transaction'),
    path('get_credit_transactions/', views.getCreditTransactionsAPI, name='get_credit_transactions'),
    path('get_transactions_summary_report/', views.getTransactionsSummaryReportAPI, name='get_transactions_summary_report'),
    path('delete_supplier_opbal_dtls_modal/', views.deleteSupplierOpBalDtlsModalAPI, name='delete_supplier_opbal_dtls_modal'),
    path('supplier_opbal_dtls_delete/<int:credit_id>/', views.supplierOpBalDtlsDeleteAPI, name='supplier_opbal_dtls_delete'),
    # payment url
    path('supplier_client_payments_services/', views.supplierClientPaymentsAPI, name='supplier_client_payments_services'),
    path('get_supplier_payment_dtls_data/', views.getSupplierPaymentDtlsDataAPI, name='get_supplier_payment_dtls_data'),
    path('save_supplier_payment_transaction/', views.saveSupplierPaymentTransactionAPI, name='save_supplier_payment_transaction'),
    # supplier report url
    path('suppliers_ledger_report_lists/', views.supplierLedgerReportListsAPI, name='suppliers_ledger_report_lists'),
    path('get_supplier_ledger_report_lists/', views.getSuppLedgerReportListsAPI, name='get_supplier_ledger_report_lists'),
    path('supplier_clients_details_reports/<int:supplier_id>/', views.supplierClientsDetailsReportsAPI, name="supplier_clients_details_reports"),
]