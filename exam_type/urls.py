from django.urls import path
from . import views

urlpatterns = [
    path('exam_type_save_and_update/', views.examTypeSaveandUpdateManagerAPI, name='exam_type_save_and_update'),
    path('get_list_of_exam_type_data/', views.getExamTypeDataManagerAPI, name='get_list_of_exam_type_data'),
    path('select_exam_type_data/<int:exam_type_id>/', views.selectExamTypeDataManagerAPI, name='select_exam_type_data'),
]