from django.urls import path
from . import views

urlpatterns = [
    path('student_attendant_list/', views.studentAttendantListManagerAPI, name='student_attendant_list'),
    path('add_new_student_attendant/', views.addNewStudentAttendantManagerAPI, name='add_new_student_attendant'),
    path('edit_student_attendants/', views.editStudentAttendantManagerAPI, name='edit_student_attendants'),
    path('update_student_attendant/', views.updateStudentAttendantManagerAPI, name='update_student_attendant'),
    path('get_student_attendant_details/', views.get_attendant_details, name='get_student_attendant_details'),
    path('save_student_attendant/', views.saveStudentAttendantManagerAPI, name='save_student_attendant'),
    path('get_student_attendant_list/', views.getStudentAttendantListManagerAPI, name='get_student_attendant_list'),
    path('get_half_and_annual_data_exist_or_not/', views.getHalfAndAnnualDataExistorNotManagerAPI, name='get_half_and_annual_data_exist_or_not'),
]