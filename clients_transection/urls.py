from django.urls import path
from . import views

urlpatterns = [
    path('opening_balance_manager_services/', views.openingBalanceManagerAPI, name='opening_balance_manager_services'),
    path('get_registration_list/', views.getRegistrationsListAPI, name='get_registration_list'),
    path('select_registration_list/<int:reg_id>/', views.selectRegistrationListAPI, name='select_registration_list'),
    path('save_opbalance_transaction/', views.saveOpBalanceTransactionAPI, name='save_opbalance_transaction'),
    path('get_opening_balances_amount/', views.getOpeningBalancesAmountAPI, name='get_opening_balances_amount'),
]
