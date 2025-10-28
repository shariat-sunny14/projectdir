from django.urls import path
from . import views

urlpatterns = [
    path('collections_reports/', views.collectionsReportManagerAPI, name='collections_reports'),
    path('collections_details_reports/', views.collectionsDetailsReportManagerAPI, name='collections_details_reports'),
    path('get_collections_report_values/', views.collectionsReportAPI, name='get_collections_report_values'),
    # sales due collection
    path('sales_due_collection_report/', views.salesDueCollectionReportAPI, name='sales_due_collection_report'),
    path('get_sales_due_collection_report/', views.getsalesDueCollectionReportManagerAPI, name='get_sales_due_collection_report'),
    path('sales_due_coll_details_report/', views.salesDueCollDetailsReportManagerAPI, name='sales_due_coll_details_report'),
    # Billing Report Dashboard Manager
    path('billing_report_dashboard_manager/', views.billingReportDashboardManagerAPI, name='billing_report_dashboard_manager'),
    path('seven_days_billing_status_view/', views.sevenDaysBillingStatusViewManagerAPI, name='seven_days_billing_status_view'),
    path('report_seven_days_billing_status/', views.reportSevenDaysBillingManagerAPI, name='report_seven_days_billing_status'),
]
