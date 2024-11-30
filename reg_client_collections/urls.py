from django.urls import path
from . import views

urlpatterns = [
    path('reg_clients_collections_services/', views.regClientsCollectionManagerAPI, name='reg_clients_collections_services'),
    path('get_reg_client_due_invoice/', views.getRegClientInvoiceDueStatusAPI, name='get_reg_client_due_invoice'),
    path('reg_client_dueinvoice_details/', views.regClientwiseDueInvoiceDetailsAPI, name='reg_client_dueinvoice_details'),
    path('save_regclient_duecoll_amt/', views.saveRegClientDueCollectionAmtAPI, name='save_regclient_duecoll_amt'),
]