from django.urls import path
from . import views

urlpatterns = [
    path('reg_clients_collections_services/', views.regClientsCollectionManagerAPI, name='reg_clients_collections_services'),
    path('get_reg_client_due_invoice/', views.getRegClientInvoiceDueStatusAPI, name='get_reg_client_due_invoice'),
    path('reg_client_dueinvoice_details/', views.regClientwiseDueInvoiceDetailsAPI, name='reg_client_dueinvoice_details'),
    path('save_regclient_duecoll_amt/', views.saveRegClientDueCollectionAmtAPI, name='save_regclient_duecoll_amt'),
    # without invoice collection url
    path('without_inv_collection_services/', views.withoutInvCollectionManagerAPI, name='without_inv_collection_services'),
    path('save_without_invoice_collection/', views.saveWithoutInvoiceCollectionAPI, name='save_without_invoice_collection'),
    path('lists_of_without_invoice_collections/', views.listsOfWithoutInvoiceCollectionAPI, name='lists_of_without_invoice_collections'),
    path('get_without_invoice_collection_data/', views.getWithoutInvoiceCollectionDataAPI, name='get_without_invoice_collection_data'),
    path('get_delete_without_inv_coll_model/', views.getDeleteWithoutInvCollModelAPI, name='get_delete_without_inv_coll_model'),
    path('without_inv_collection_dtl_elete/<int:wo_coll_id>/', views.withoutInvCollectionDtlDeleteAPI, name='without_inv_collection_dtl_elete'),
]