from django.urls import path
from . import views

urlpatterns = [
    path('bank_statement_list/', views.bankStatementManagerAPI, name="bank_statement_list"),
    path('get_bank_statement_list/', views.getBankStatementListsAPI, name="get_bank_statement_list"),
    path('add_bank_statement_modal/', views.addBankStatementModelManageAPI, name="add_bank_statement_modal"),
    path('add_bank_statement_deposit/', views.addBankStatementAPI, name="add_bank_statement_deposit"),
]
