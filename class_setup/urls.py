from django.urls import path
from . import views

urlpatterns = [
    path('class_save_and_update/', views.classSaveAndUpdateManagerAPI, name='class_save_and_update'),
    path('get_list_of_class_data/', views.getClassListDataManagerAPI, name='get_list_of_class_data'),
    path('get_class_lists/<int:class_id>/', views.getClassListManagerAPI, name='get_class_lists'),
]