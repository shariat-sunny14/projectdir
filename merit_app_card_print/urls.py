from django.urls import path
from . import views

urlpatterns = [
    path('merit_position_app_and_card_print_list/', views.meritPositionAppAndCardPrintManagerAPI, name='merit_position_app_and_card_print_list'),
    path('merit_position_approval/', views.meritPositionApprovalManagerAPI, name='merit_position_approval'),
    path('get_finalized_result_data_for_merit_pos/', views.getFinalizedResultDataForMeritPosAPI, name='get_finalized_result_data_for_merit_pos'),
    path('save_approve_merit_position/', views.saveApproveMeritPositionAPI, name='save_approve_merit_position'),
    path('get_merit_position_approvals_list/', views.getMeritApprovalsListManagerAPI, name='get_merit_position_approvals_list'),
    path('get_sections_list_by_class/', views.get_sections_by_class, name='get_sections_list_by_class'),
    path('merit_position_approve_list/', views.meritPositionApproveListManagerAPI, name='merit_position_approve_list'),
    path('rollback_merit_position/', views.rollbackMeritPositionManagerAPI, name='rollback_merit_position'),
    path('permanently_delete_merit_position/', views.permanently_delete_merit_positionManagerAPI, name='permanently_delete_merit_position'),
    # Report URL
    path('report_merit_position/', views.reportMeritPositionManagerAPI, name='report_merit_position'),
    path('get_merit_position_report_data/', views.getMeritPositionReportDataManagerAPI, name='get_merit_position_report_data'),
]