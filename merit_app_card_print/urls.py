from django.urls import path
from . import views

urlpatterns = [
    path('merit_position_app_and_card_print_list/', views.meritPositionAppAndCardPrintManagerAPI, name='merit_position_app_and_card_print_list'),
    path('merit_position_approval/', views.meritPositionApprovalManagerAPI, name='merit_position_approval'),
    path('get_finalized_result_data_for_merit_pos/', views.getFinalizedResultDataForMeritPosAPI, name='get_finalized_result_data_for_merit_pos'),
    path('save_approve_merit_position/', views.saveApproveMeritPositionAPI, name='save_approve_merit_position'),
    path('get_merit_position_approvals_list/', views.getMeritApprovalsListManagerAPI, name='get_merit_position_approvals_list'),
    path('get_sections_list_by_class/', views.get_sections_by_class, name='get_sections_list_by_class'),
]