from django.urls import path
from . import views

urlpatterns = [
    path('order_list/', views.orderListViewManagerAPI, name='order_list'),
    path('orders_listed/', views.orderListViewFromWebsiteManagerAPI, name='orders_listed'),
    path('get_order_list/', views.getOrderListManagerAPI, name='get_order_list'),
    path('get_order_list_by_user/', views.getOrderListByUserIdManagerAPI, name='get_order_list_by_user'),
    path('view_order_modal/', views.viewOrderModalManagerAPI, name='view_order_modal'),
    path('order_submit_api/', views.orderSubmitManagerAPI, name='order_submit_api'),
]
