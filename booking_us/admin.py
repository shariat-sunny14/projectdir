from django.contrib import admin
from .models import EventSchedule

@admin.register(EventSchedule)
class EventScheduleAdmin(admin.ModelAdmin):
    list_display = ['schedule_id', 'slot_id', 'event_date', 'status']

