from django.urls import path
from . import views

urlpatterns = [
    path('defaults_exam_modes_setup/', views.defaultsExamModesSetupManagerAPI, name='defaults_exam_modes_setup'),
    path('save_defaults_exam_modes/', views.saveDefaultsExamModesSetupManagerAPI, name='save_defaults_exam_modes'),
    path('get_exam_modes_combined/', views.get_exam_modes_combinedAPI, name='get_exam_modes_combined'),
    path('get_exam_modes_list/', views.getExamModesListManagerAPI, name='get_exam_modes_list'),
]