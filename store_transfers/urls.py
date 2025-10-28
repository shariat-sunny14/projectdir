from django.urls import path
from . import views

urlpatterns = [
    path('stock_store_transfer_list_services/', views.storeTransferListManagerAPI, name='stock_store_transfer_list_services'),
    path('add_new_store_transfer_services/', views.addNewStoreTransferManagerAPI, name='add_new_store_transfer_services'),
    path('get_stock_transfer_item_list/', views.getStockTransferItemListAPI, name='get_stock_transfer_item_list'),
    path('save_store_to_store_transfer/', views.saveStoreTransferManagerAPI, name='save_store_to_store_transfer'),
    path('get_store_transfer_list/', views.getStoreTransferListManagerAPI, name='get_store_transfer_list'),
    path('edit_update_store_transfer_form/', views.editStoreTransferFormManagerAPI, name='edit_update_store_transfer_form'),
    path('get_stock_transfer_edit_from_data/', views.getStockTransferDataEditFromManagerAPI, name='get_stock_transfer_edit_from_data'),
    path('delete_transfer_dtl/<int:stock_transdtl_id>/', views.deletetransfer_listdtlManagerAPI, name='delete_transfer_dtl'),
    path('edit_update_stock_transfer_data/', views.editUpdateStockTransferDataManagerAPI, name='edit_update_stock_transfer_data'),
    path('store_transfer_reports_dtls/', views.storeTransferReportsManagerAPI, name='store_transfer_reports_dtls'),

]