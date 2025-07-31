from django.urls import path
from . import views

urlpatterns = [
    path('shifts_save_and_update/', views.shiftsSaveandUpdateManagerAPI, name='shifts_save_and_update'),
    path('get_list_of_shifts_data/', views.getShiftsDataManagerAPI, name='get_list_of_shifts_data'),
    path('select_shifts_data/<int:shift_id>/', views.selectShiftsDataManagerAPI, name='select_shifts_data'),
]