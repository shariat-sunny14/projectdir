from django.urls import path
from . import views

urlpatterns = [
    path('collections_reports/', views.collectionsReportManagerAPI, name='collections_reports'),
    path('collections_details_reports/', views.collectionsDetailsReportManagerAPI, name='collections_details_reports'),
    path('get_collections_report_values/', views.collectionsReportAPI, name='get_collections_report_values'),
]
