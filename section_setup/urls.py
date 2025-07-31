from django.urls import path
from . import views

urlpatterns = [
    path('section_save_and_update/', views.sectionSaveandUpdateManagerAPI, name='section_save_and_update'),
    path('get_list_of_section_data/', views.getSectionDataManagerAPI, name='get_list_of_section_data'),
    path('select_section_data/<int:section_id>/', views.selectSectionDataManagerAPI, name='select_section_data'),
]