from django.urls import path
from . import views

urlpatterns = [
    path('opening_balance_manager_services/', views.openingBalanceManagerAPI, name='opening_balance_manager_services'),
    path('reg_clients_payment_services/', views.regClientsPaymentManagerAPI, name='reg_clients_payment_services'),
    path('get_registration_list/', views.getRegistrationsListAPI, name='get_registration_list'),
    path('select_registration_list/<int:reg_id>/', views.selectRegistrationListAPI, name='select_registration_list'),
    path('save_opbalance_transaction/', views.saveOpBalanceTransactionAPI, name='save_opbalance_transaction'),
    path('save_reg_clients_payment_transaction/', views.saveregClientsPaymentTransactionAPI, name='save_reg_clients_payment_transaction'),
    path('get_opening_balances_amount/', views.getOpeningBalancesAmountAPI, name='get_opening_balances_amount'),
    path('get_payment_details_data/', views.getpaymentDtlsDataAPI, name='get_payment_details_data'),
    path('opening_balances_details_delete/<int:opb_id>/', views.openingBalancesDetailsDeleteAPI, name='opening_balances_details_delete'),
    path('payment_details_delete/<int:pay_id>/', views.paymentDetailsDeleteAPI, name='payment_details_delete'),
    path('delete_payment_details_modal/', views.deletepaymentDetailsModalAPI, name='delete_payment_details_modal'),
    path('delete_opening_balances_details_modal/', views.deleteopeningBalancesDetailsModalAPI, name='delete_opening_balances_details_modal'),
]
