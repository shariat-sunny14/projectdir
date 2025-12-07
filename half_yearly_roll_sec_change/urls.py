from django.urls import path
from . import views

urlpatterns = [
    path('half_yearly_roll_section_changes_list/', views.halfYearlyRollSecChangeListManagerAPI, name='half_yearly_roll_section_changes_list'),
    path('half_yearly_roll_section_changing/', views.halfYearlyRollSecChangingManagerAPI, name='half_yearly_roll_section_changing'),
    path('get_merit_appr_for_half_yearly_roll_section_change_list/', views.getMeritApprovalsForHYRSCListManagerAPI, name='get_merit_appr_for_half_yearly_roll_section_change_list'),
    path('get_details_info_for_half_yearly_roll_sec_change_data/', views.getMeritPositionDetailsForHalfYearlyRollSecChangeAPI, name='get_details_info_for_half_yearly_roll_sec_change_data'),
    path('save_half_yearly_roll_section_change/', views.saveHalfYearlyRollSectionChangeManagerAPI, name='save_half_yearly_roll_section_change'),
    path('half_yearly_roll_sec_change_rollback/', views.halfYearlyRollSecChangeRollbackListManagerAPI, name='half_yearly_roll_sec_change_rollback'),
    path('get_half_yearly_roll_sec_change_rollback_list/', views.getHalfYearlyRollSecChangeRollbacklistAPI, name='get_half_yearly_roll_sec_change_rollback_list'),
    path('half_yearly_roll_sec_changing_rollback/', views.halfYearlyRollSecChangingRollBackManagerAPI, name='half_yearly_roll_sec_changing_rollback'),
    # report view
    path('Report_half_yearly_roll_section_change/', views.ReportHalfYearlyRollSecChangeAPI, name='Report_half_yearly_roll_section_change'),
    path('get_details_for_report_half_yearly_roll_section_change/', views.getDetailsForReportHalfYearlyRollSecChangeAPI, name='get_details_for_report_half_yearly_roll_section_change'),
    # rollback processing view
    path('get_details_for_half_yearly_roll_sec_change_rollback/', views.getDetailsForHalfYearlyRollSecChangeRollbackAPI, name='get_details_for_half_yearly_roll_sec_change_rollback'),
    path('rollback_half_yearly_roll_section_change/', views.rollbackHalfYearlyRollSectionChangeAPI, name='rollback_half_yearly_roll_section_change'),
    # rollback history list view
    path('half_yearly_roll_sec_change_rollback_history_list/', views.halfYearlyRollSecChangeRollbackHistoryListAPI, name='half_yearly_roll_sec_change_rollback_history_list'),
    path('get_half_yearly_roll_sec_change_rollback_history_list/', views.getHalfYearlyRollSecChangeRollbackHistoryListAPI, name='get_half_yearly_roll_sec_change_rollback_history_list'),
    # report rollback history view
    path('Report_half_yearly_roll_section_change_rollback_history/', views.reportHalfYearlyRollSecChangeRollbackHistoryAPI, name='Report_half_yearly_roll_section_change_rollback_history'),
    path('get_details_for_report_half_yearly_roll_sec_change_rollback_his/', views.getDetailsForReportHalfYearlyRollSecChangeRollbackHistoryAPI, name='get_details_for_report_half_yearly_roll_sec_change_rollback_his'),
]