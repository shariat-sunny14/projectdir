from django.urls import path
from . import views

urlpatterns = [
    path('others_bank_bkash_etc_collection_summary_report/', views.othersBankBkashEtcCollectionSummaryReportAPI, name='others_bank_bkash_etc_collection_summary_report'),
    path('previous_remaining_from_total_net_collection/', views.previousRemainingFromTotalNetCollectionAPI, name='previous_remaining_from_total_net_collection'),
    path('present_to_seven_days_collection_summary_report/', views.presentToSevenDaysCollectionSummaryReportAPI, name='present_to_seven_days_collection_summary_report'),
]