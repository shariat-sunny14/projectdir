from django.urls import path
from . import views

urlpatterns = [
    path('statistics_dashboard/', views.statisticsDashboardManagerAPI, name='statistics_dashboard'),
    path('statistics_app_summary/', views.statisticsAppSummaryManagerAPI, name='statistics_app_summary'),
    path('get_students_address_info/', views.getStudentsAddressManagerAPI, name='get_students_address_info'),
    path('get_exam_sms_summary_status/', views.getExamSMSSummaryStatusManagerAPI, name='get_exam_sms_summary_status'),
    path('get_students_total_marks/', views.getStudentsTotalMarksManagerAPI, name='get_students_total_marks'),
    path('get_students_particular_tops_marks/', views.getStudentsParticularTopsMarksManagerAPI, name='get_students_particular_tops_marks'),
    path('get_section_wise_student_info/', views.getSectionWiseStudentInfoAPI, name='get_section_wise_student_info'),
    path('get_shift_wise_student_info/', views.getShiftWiseStudentInfoManagerAPI, name='get_shift_wise_student_info'),
    path('get_group_wise_student_info/', views.getGroupWiseStudentInfoManagerAPI, name='get_group_wise_student_info'),
    # path('get_section_shift_groups_student_info/', views.getSectionShiftGroupsStudentInfoManagerAPI, name='get_section_shift_groups_student_info'),
    path('get_class_wise_student_summary/', views.getClasswiseStudentSummaryManagerAPI, name='get_class_wise_student_summary'),
    path('get_yearly_month_wise_sms_tatus/', views.getYearlyMonthWiseSMSStatusManagerAPI, name='get_yearly_month_wise_sms_tatus'),
]