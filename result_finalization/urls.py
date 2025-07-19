from django.urls import path
from . import views

urlpatterns = [
    path('result_finalization_list/', views.resultFinalizationListManagerAPI, name='result_finalization_list'),
    path('result_finalize_services/', views.grossResultFinalizeManagerAPI, name='result_finalize_services'),
    path('edit_result_finalize_services/<int:res_fin_id>/', views.editGrossResultFinalizeManagerAPI, name='edit_result_finalize_services'),
    path('get_subjects_options/', views.getSubjectsOptionsManagerAPI, name='get_subjects_options'),
    path('get_defaults_exam_modes_by_class/', views.getDefaultsExamModesManagerAPI, name='get_defaults_exam_modes_by_class'),
    path('get_reg_list_details_for_finalized_results/', views.getRegListDetailsForFinalizedResultsAPI, name='get_reg_list_details_for_finalized_results'),
    path('save_results_finalization/', views.saveResultsFinalizationManagerAPI, name='save_results_finalization'),
    path('get_results_finalization_list/', views.getResultsFinalizationListManagerAPI, name='get_results_finalization_list'),
]