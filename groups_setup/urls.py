from django.urls import path
from . import views

urlpatterns = [
    path('groups_save_and_update/', views.groupsSaveandUpdateManagerAPI, name='groups_save_and_update'),
    path('get_list_of_groups_data/', views.getGroupsDataManagerAPI, name='get_list_of_groups_data'),
    path('select_groups_data/<int:groups_id>/', views.selectGroupsDataManagerAPI, name='select_groups_data'),
]