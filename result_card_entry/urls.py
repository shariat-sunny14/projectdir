from django.urls import path
from . import views

urlpatterns = [
    path('result_card_entry_services/', views.resultCardEntryListManagerAPI, name='result_card_entry_services'),
    path('result_card_re_print_list/', views.resultCardEntryRePrintListManagerAPI, name='result_card_re_print_list'),
    path('get_registration_list_details/', views.getRegistrationListDetailsAPI, name='get_registration_list_details'),
    path('get_result_card_entry_re_print_details/', views.getResultCardEntryRePrintDetailsListAPI, name='get_result_card_entry_re_print_details'),
    path('get_results_entry_from/', views.getResultsEntryUIManagerAPI, name='get_results_entry_from'),
    path('save_results_card_entry/', views.saveResultsCardEntryManagerAPI, name='save_results_card_entry'),
    path('results_card_entry_report/', views.resultsCardEntryReportManagerAPI, name='results_card_entry_report'),
    path('print_results_card_entry_report/', views.printResultsCardEntryReportManagerAPI, name='print_results_card_entry_report'),
    path('print_transcript/', views.print_transcript, name='print_transcript'),
    path('print_multiple_transcripts/', views.print_multiple_transcripts, name='print_multiple_transcripts'),
    path('testing_api/', views.testingAPI, name='testing_api'),
]