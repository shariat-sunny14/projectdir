from django.urls import path
from . import views

urlpatterns = [
    path('defaults_exam_modes_setup/', views.defaultsExamModesSetupManagerAPI, name='defaults_exam_modes_setup'),
    path('save_defaults_exam_modes_setup/', views.saveDefaultsExamModesSetupManagerAPI, name='save_defaults_exam_modes_setup'),
    path('get_defaults_exam_modes/', views.getDefaultsExamModesManagerAPI, name='get_defaults_exam_modes'),
    path('select_defaults_exam_modes/<int:class_id>/', views.selectDefaultsExamModesManagerAPI, name='select_defaults_exam_modes'),
]