from django.urls import path
from . import views

urlpatterns = [
    path('subjects_save_and_update/', views.subjectsSaveandUpdateManagerAPI, name='subjects_save_and_update'),
    path('get_list_of_subjects_data/', views.getSubjectsDataManagerAPI, name='get_list_of_subjects_data'),
    path('select_subjects_data/<int:subjects_id>/', views.selectSubjectsDataManagerAPI, name='select_subjects_data'),
]