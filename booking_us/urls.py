from django.urls import path
from . import views

urlpatterns = [
    path('schedule_list/', views.scheduleListManagerAPI, name='schedule_list'),
    path('add_schedule_modal/', views.addScheduleModalManagerAPI, name='add_schedule_modal'),
    path('add_schedule/', views.addScheduleManagerAPI, name='add_schedule'),
    path('get_schedules/', views.get_schedulesAPI, name='get_schedules'),
    path('get_schedule_list/', views.getScheduleListManagerAPI, name='get_schedule_list'),
    path('delete_schedule_list/', views.delete_schedule_listAPI, name='delete_schedule_list'),
    path('booking_from_package/', views.bookingFromPackageManagerAPI, name='booking_from_package'),
]
