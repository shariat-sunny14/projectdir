from django.urls import path
from . import views

urlpatterns = [
    path('result_card_entry_services/', views.resultCardEntryListManagerAPI, name='result_card_entry_services'),
    path('result_card_entry_history_list/', views.resultCardEntryHistoryListManagerAPI, name='result_card_entry_history_list'),
    path('get_registration_list_details/', views.getRegistrationListDetailsAPI, name='get_registration_list_details'),
    path('get_result_card_history_details_list/', views.getResultCardHistoryDetailsListAPI, name='get_result_card_history_details_list'),
    path('get_results_entry_from/', views.getResultsEntryUIManagerAPI, name='get_results_entry_from'),
    path('get_half_yearly_result/', views.getHalfYearlyResultAPI, name='get_half_yearly_result'),
    path('save_results_card_entry/', views.saveResultsCardEntryManagerAPI, name='save_results_card_entry'),
    path('results_card_entry_report/', views.resultsCardEntryReportManagerAPI, name='results_card_entry_report'),
    path('print_results_card_entry_report/', views.printResultsCardEntryReportManagerAPI, name='print_results_card_entry_report'),
    path('print_transcript/', views.print_transcript, name='print_transcript'),
    path('print_multiple_transcripts/', views.print_multiple_transcripts, name='print_multiple_transcripts'),
    path('testing_api/', views.testingAPI, name='testing_api'),
    path('get_student_attendance/', views.getStudentAttendance, name='get_student_attendance'),
    # annual result entry UI
    path('get_annual_results_entry_from/', views.getannualResultsEntryUIManagerAPI, name='get_annual_results_entry_from'),
    path('get_is_annual_details_result_api/', views.getisAnnualDetailsResultAPI, name='get_is_annual_details_result_api'),
    path('get_student_attendance_annual_examination/', views.getStudentAttendanceAnnualExaminationAPI, name='get_student_attendance_annual_examination'),
    path('save_annual_results_card_entry/', views.saveAnnualResultsCardEntryManagerAPI, name='save_annual_results_card_entry'),
    path('annual_results_card_entry_viewer/', views.annualResultsCardEntryViewerManagerAPI, name='annual_results_card_entry_viewer'),
    path('annual_results_card_reports/', views.annualResultsCardReportsManagerAPI, name='annual_results_card_reports'),
    path('print_is_annual_details_result/', views.printisAnnualDetailsResultAPI, name='print_is_annual_details_result'),
    # individual annual report card
    path('individual_report_annual_results_card/', views.individualReportAnnualResultsCardAPI, name='individual_report_annual_results_card'),
    path('rollback_results_card/', views.rollbackResultsCardManagerAPI, name='rollback_results_card'),
    path('rollback_results_card_submission/', views.rollbackResultsCardSubmissionAPI, name='rollback_results_card_submission'),
]