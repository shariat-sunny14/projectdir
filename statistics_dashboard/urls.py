from django.urls import path
from . import views

app_name = 'statistics_dashboard'

urlpatterns = [
    path('get_statistics_total_cash_coll_report/', views.statisticsTotalCashCollReportAPI, name='get_statistics_total_cash_coll_report'),
    path('get_statistics_total_sales_report/', views.statisticsTotalSalesReportAPI, name='get_statistics_total_sales_report'),
    path('get_statistics_total_dues_report/', views.statisticsTotalDuesReportAPI, name='get_statistics_total_dues_report'),
]
