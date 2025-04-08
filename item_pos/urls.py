from django.urls import path
from . import views

urlpatterns = [
    path('item_pos_billing/', views.item_posAPI, name='pos_billing'),
    path('get_item_list/', views.get_item_listAPI, name='get_item_list'),
    path('get_itemlist_without_item_no/', views.getItemListWithItemNameAPI, name='get_itemlist_without_item_no'),
    path('select_item_value/', views.select_item_listAPI, name='select_item_value'),
    path('select_item_without_stock_list/', views.selectItemWithoutStocklistAPI, name='select_item_without_stock_list'),
    # 
    path('get_item_list_with_sumtotal_stock/', views.getItemListWithSumTotalStockAPI, name='get_item_list_with_sumtotal_stock'),
    path('select_item_list_with_sumtotal_stock/', views.selectItemListWithSumTotalStockAPI, name='select_item_list_with_sumtotal_stock'),
    # 
    path('save_pos_billing/', views.saveBoardStoreInvoiceAPI, name='save_pos_billing'),
    path('save_grocery_store_pos_billing/', views.saveGroceryStoreInvoiceAPI, name='save_grocery_store_pos_billing'),
    path('save_pharmacy_pos_bill/', views.savePharmacyPOSManagerAPI, name='save_pharmacy_pos_bill'),
    path('receipt/', views.receipt, name="receipt_modal"),
    path('search_b2b_clients_for_billing/', views.searchb2bClientsInBillingAPI, name="search_b2b_clients_for_billing"),
    path('select_b2b_clients_details/', views.selectB2bClientsDetailsAPI, name="select_b2b_clients_details"),
    path('rent_others_expense_list/', views.rentOthersExpsManagerAPI, name="rent_others_expense_list"),
    path('get_others_expense_list/', views.getRentOthersExpsListsAPI, name="get_others_expense_list"),
    path('add_carrying_expenses_modal/', views.addExpensesModelManageAPI, name="add_carrying_expenses_modal"),
    path('add_expenses_bill/', views.addExpenseAPI, name="add_expenses_bill"),
    path('save_favorite_item/', views.saveFavoriteItemManagerAPI, name='save_favorite_item'),
    path('get_fav_item_list/', views.getFavItemListManagerAPI, name='get_fav_item_list'),
    path('delete_fav_item/<int:fav_id>/', views.delete_fav_item, name='delete_fav_item'),
    path('add_items_in_pos_billing/', views.itemAddInPosBillingUpdateManagerAPI, name="add_items_in_pos_billing"),
    path('add_items_pos_update_invoice/', views.addItemPosUpdateInvManagerAPI, name="add_items_pos_update_invoice"),
    path('get_reward_point_balance/', views.getRewardPointBalanceAPI, name="get_reward_point_balance"),
    path('add_new_reg_pos/', views.addNewRegistrationManagerAPI, name="add_new_reg_pos"),
    path('barcode_wise_select_items/', views.selectAutomaticItemWithBarcodeAPI, name="barcode_wise_select_items"),
    path('open_reward_point_modal/', views.openRewardPointModalAPI, name="open_reward_point_modal"),
    path('add_reward_point/', views.addRewardPointManagerAPI, name="add_reward_point"),
    # carrying cost url
    path('carrying_cost_payment_services/', views.carryingCostPaymentManagerAPI, name="carrying_cost_payment_services"),
    path('save_carrying_payment_bill/', views.saveCarryingPaymentBillAPI, name="save_carrying_payment_bill"),
    path('get_carrier_payment_lists/', views.getCarrierPaymentListsAPI, name="get_carrier_payment_lists"),
    path('get_delete_carrying_cost_pay_model/', views.getDeleteCarryingCostPayModelAPI, name="get_delete_carrying_cost_pay_model"),
    path('carrying_cost_payments_dtl_delete/<int:c_cost_id>/', views.carryingCostPaymentsDtlDeleteAPI, name='carrying_cost_payments_dtl_delete'),
]
