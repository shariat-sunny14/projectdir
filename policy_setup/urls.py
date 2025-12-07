from django.urls import path
from . import views

urlpatterns = [
    path('letter_grade_exam_type_policy_setups/', views.policySetupManagerAPI, name='letter_grade_exam_type_policy_setups'),
    path('letter_grade_xm_type_policy_save_update/', views.letterGradeXMtypePolicySaveandUpdate, name='letter_grade_xm_type_policy_save_update'),
    path('get_lg_xmtype_policy_setup_data/', views.getPolicySetupDataManagerAPI, name='get_lg_xmtype_policy_setup_data'),
    path('merit_positions_policy_setup/', views.meritPositionsPolicyManagerAPI, name='merit_positions_policy_setup'),
    path('get_class_wise_merit_policy_data/', views.getclassWiseMeritPolicyManagerAPI, name='get_class_wise_merit_policy_data'),
    path('save_classwise_merit_policy/', views.save_classwise_merit_policy, name='save_classwise_merit_policy'),
    path('save_subjectswise_merit_policy/', views.save_subjectswise_merit_policy, name='save_subjectswise_merit_policy'),
    path('get_subjectswise_merit_policy/', views.get_subjectswise_merit_policy, name='get_subjectswise_merit_policy'),
    path('delete_subjectswise_policy/', views.delete_subjectswise_policy, name='delete_subjectswise_policy'),
    path('save_class_section_grouping/', views.save_class_section_grouping, name='save_class_section_grouping'),
    path('get_class_section_grouping_for_english/', views.get_class_section_grouping_for_english, name='get_class_section_grouping_for_english'),
    path('get_class_section_grouping_for_bangla/', views.get_class_section_grouping_for_bangla, name='get_class_section_grouping_for_bangla'),
    # half year roll sec change policy
    path('half_year_roll_sec_change_policy/', views.halfYearRollSecChangePolicyManagerAPI, name='half_year_roll_sec_change_policy'),
    path('save_half_year_roll_section_change_policy/', views.savehalfYearRollSecChangePolicyManagerAPI, name='save_half_year_roll_section_change_policy'),
    path('get_halfyear_roll_policy/', views.get_halfyear_roll_policyManagerAPI, name='get_halfyear_roll_policy'),
    path('get_in_section_data/', views.get_in_section_dataManagerAPI, name='get_in_section_data'),
    # annual exam policy
    path('annual_exam_percentance_policy/', views.annualExamPercentancePolicyManagerAPI, name='annual_exam_percentance_policy'),
    path('save_annual_exam_percentance_policy/', views.saveAnnualExamPercentancePolicyAPI, name='save_annual_exam_percentance_policy'),
    path('get_annual_exam_percentance_policy_list/', views.getAnnualExamPercentancePolicyListAPI, name='get_annual_exam_percentance_policy_list'),
]