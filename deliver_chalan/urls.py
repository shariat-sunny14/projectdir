from django.urls import path
from . import views

urlpatterns = [
    path('delivery_chalan_services/', views.deliveryChalanManagerAPI, name='delivery_chalan_services'),
    path('manual_delivery_chalan_service/', views.manualDeliveryChalanManagerAPI, name='manual_delivery_chalan_service'),
    path('fetch_delivery_chalan_pending/', views.fetchDeliveryChalanPendingDataAPI, name='fetch_delivery_chalan_pending'),
    path('fetch_delivery_chalan_data/', views.fetchDeliveryChalanDataAPI, name='fetch_delivery_chalan_data'),
    path('update_delivery_chalan/<int:inv_id>/', views.updateDeliveryChalanAPI, name='update_delivery_chalan'),
    path('get_delivery_chalan_data/', views.getDeliveryChalanDataAPI, name='get_delivery_chalan_data'),
    path('save_update_delivery_chalan/', views.saveandUpdateDeliveryChalanAPI, name='save_update_delivery_chalan'),
    path('delivery_chalan/', views.deliveryChalan, name="chalan_modal"),
    path('delivery_chalan_modified_items/', views.deliveryChalanModifiedItems, name="delivery_chalan_modified_items"),
    path('manual_delivery_chalan_receipts/', views.manualDeliveryChalanReceipts, name="manual_delivery_chalan_receipts"),
    path('delete_chalan_details_items_wise/<int:invdtl_id>/', views.deleteChalanDetailsItemsWiseAPI, name='delete_chalan_details_items_wise'),
    # //
    path('get_all_store_for_manual_delivery_chalan/', views.getAllStoreForManualDeliveryChalanAPI, name='get_all_store_for_manual_delivery_chalan'),
    # //
    path('save_manual_delivery_chalan/', views.saveManualDeliveryChalanAPI, name='save_manual_delivery_chalan'),
    path('edit_update_manual_delivery_chalan/<int:chalan_id>/', views.editUpdateManualDeliveryChalanManagerAPI, name='edit_update_manual_delivery_chalan'),
    path('get_manual_delivery_info/', views.getManualDeliveryInfoAPI, name='get_manual_delivery_info'),
    path('delete_manual_chalan_dtls/<int:chanaldtl_id>/', views.deleteManualDeliveryChalanDtlsAPI, name='delete_manual_chalan_dtls'),
    path('update_manual_delivery_chalan/', views.updateManualDeliveryChalanAPI, name='update_manual_delivery_chalan'),
]
